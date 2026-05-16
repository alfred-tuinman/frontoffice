import "dotenv/config";
import express from 'express';
import path from 'path';
import nunjucks from 'nunjucks';
import multer from 'multer';
import session from 'express-session';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import fs from 'fs';

const PORT = 3010;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);


const app = express();

// ------------------------- 
// SESSION
// -------------------------
app.use(session({
    secret: 'booking_secret',
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false } // set to true if using HTTPS
}));

// -------------------------
// NUNJUCKS
// -------------------------
const env = nunjucks.configure('templates', {
    autoescape: true,
    express: app
});

// Add date converter filter: DD.MM.YYYY -> YYYY-MM-DD
env.addFilter('formatDate', (dateStr) => {
    if (!dateStr || typeof dateStr !== 'string') return '';
    const match = dateStr.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
    if (match) {
        return `${match[3]}-${match[2]}-${match[1]}`;
    }
    return dateStr; // Return unchanged if not matching format
});

// -------------------------
// STATIC FILES
// -------------------------
app.use('/static', express.static(
    path.join(__dirname, 'static')
));

// -------------------------
// FILE UPLOADS
// -------------------------
const upload = multer({
    dest: 'uploads/'
});

// -------------------------
// ROUTES
// -------------------------

app.get('/', (req, res) => {

    res.send(
        nunjucks.render('index.html', {
            title: 'Home'
        })
    );
});

app.get('/index.html', (req, res) => {

    res.redirect('/');
});

app.get('/review', (req, res) => {
    const parsed = req.session.parsed || {};
    req.session.parsed = null; // clear after use
    res.send(
        nunjucks.render('review.html', {
            title: 'Review',
            q: parsed
        })
    );
});

app.get('/success', (req, res) => {

    res.send(
        nunjucks.render('success.html', {
            title: 'Success'
        })
    );
});

// -------------------------
// UPLOAD ROUTE
// -------------------------
app.post('/upload', upload.single('pdf'), (req, res) => {
    console.log('Uploaded file:', req.file);

    if (!req.file) {
        return res.status(400).send('No file uploaded.');
    }

    const tempPdfPath = req.file.path;

    // Call the Python parser to get JSON for the review form
    const pythonProcess = spawn('python', [
        path.join(__dirname, 'parse_booking.py'),
        tempPdfPath
    ]);

    let output = '';
    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    let errorOutput = '';
    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.error('Python script error:', errorOutput);
            return res.status(500).send('Error parsing PDF.');
        }
        let parsedData;
        try {
            parsedData = JSON.parse(output);
        } catch (e) {
            console.error('JSON parse error:', output);
            return res.status(500).send('Invalid parser output.');
        }
        console.log('✅ Parsed booking data:', JSON.stringify(parsedData, null, 2));

        // Create a booking-specific folder
        const bookingRef = parsedData.QuotationRef || `booking_${Date.now()}`;
        const bookingFolder = path.join('uploads', bookingRef);
        
        if (!fs.existsSync(bookingFolder)) {
            fs.mkdirSync(bookingFolder, { recursive: true });
        }

        // Save PDF with proper extension
        const pdfFileName = `${bookingRef}.pdf`;
        const pdfPath = path.join(bookingFolder, pdfFileName);
        fs.copyFileSync(tempPdfPath, pdfPath);
        fs.unlinkSync(tempPdfPath); // Remove temp file
        console.log('✅ PDF saved:', pdfPath);

        // Generate Excel
        const excelFileName = `${bookingRef}.xlsx`;
        const excelPath = path.join(bookingFolder, excelFileName);

        const excelProcess = spawn('python', [
            path.join(__dirname, 'build_excel_wrapper.py'),
            pdfPath,
            excelPath
        ]);

        let excelOutput = '';
        let excelError = '';
        excelProcess.stdout.on('data', (data) => {
            excelOutput += data.toString();
        });
        excelProcess.stderr.on('data', (data) => {
            excelError += data.toString();
        });

        excelProcess.on('close', (excelCode) => {
            if (excelCode === 0) {
                console.log('✅ Excel generated:', excelPath);
                console.log('  Output:', excelOutput);
            } else {
                console.warn('⚠️  Excel generation warning:', excelError);
                // Don't fail the request — just log the warning
            }

            req.session.parsed = parsedData;
            req.session.excelFile = excelPath;
            req.session.bookingFolder = bookingFolder;
            
            try {
                const html = nunjucks.render('review.html', {
                    title: 'Review',
                    q: parsedData,
                    excelFile: excelPath,
                    bookingFolder: bookingFolder
                });
                console.log('✅ Review page rendered successfully');
                res.send(html);
            } catch (renderError) {
                console.error('Template render error:', renderError);
                res.status(500).send('Error rendering review page: ' + renderError.message);
            }
        });
    });
});

// -------------------------
// DOWNLOAD EXCEL
// -------------------------
app.get('/download/excel', (req, res) => {
    const excelFile = req.session.excelFile;
    if (!excelFile) {
        return res.status(404).send('Excel file not found in session.');
    }
    const fileName = path.basename(excelFile);
    res.download(excelFile, fileName, (err) => {
        if (err) {
            console.error('Download error:', err);
        }
    });
});

// -------------------------
// 404
// -------------------------
app.use((req, res) => {

    res.status(404).send('404 Not Found');
});

// -------------------------
// START SERVER
// -------------------------
app.listen(PORT, () => {

    console.log(`http://localhost:${PORT}`);
});