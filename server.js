import "dotenv/config";
import express from 'express';
import path from 'path';
import nunjucks from 'nunjucks';
import multer from 'multer';
import session from 'express-session';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import fs from 'fs';
import crypto from 'crypto';

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
// MIDDLEWARE
// -------------------------
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

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
    
    // Generate a token for this form submission
    const token = crypto.randomBytes(16).toString('hex');
    req.session.formToken = token;
    
    res.send(
        nunjucks.render('review.html', {
            title: 'Review',
            q: parsed,
            token: token,
            excelFile: req.session.excelFile || null
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
        path.join(__dirname, 'python', 'parse_booking.py'),
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
            path.join(__dirname, 'python', 'build_excel_wrapper.py'),
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
            
            // Generate a token for this form submission
            const token = crypto.randomBytes(16).toString('hex');
            req.session.formToken = token;
            
            console.log('📊 excelPath:', excelPath);
            console.log('📊 exists:', fs.existsSync(excelPath));
            try {
                const html = nunjucks.render('review.html', {
                    title: 'Review',
                    q: parsedData,
                    excelFile: excelPath,
                    bookingFolder: bookingFolder,
                    token: token
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
// SUBMIT BOOKING
// -------------------------
app.post('/submit/:token', (req, res) => {
    console.log('📝 Form submitted with token:', req.params.token);
    console.log('📋 Form data:', req.body);

    // Prepare data for Python to save
    const bookingData = {
        ...req.body,
        QuotationDate: new Date().toISOString().split('T')[0]
    };

    // Call Python script to save to database
    const pythonProcess = spawn('python', [
        path.join(__dirname, 'python', 'save_booking.py'),
        JSON.stringify(bookingData)
    ]);

    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        output += chunk;
        console.log('📤 Python stdout:', chunk);
    });

    pythonProcess.stderr.on('data', (data) => {
        const chunk = data.toString();
        errorOutput += chunk;
        console.log('⚠️  Python stderr:', chunk);
    });

    pythonProcess.on('close', (code) => {
        console.log('🔚 Python process closed with code:', code);
        console.log('💾 Full stdout:', output);
        console.log('💾 Full stderr:', errorOutput);

        if (code !== 0) {
            console.error('❌ Database save error (exit code ' + code + '):', errorOutput);
            return res.status(500).json({ error: 'Error saving booking to database', details: errorOutput });
        }

        let result;
        try {
            result = JSON.parse(output);
        } catch (e) {
            console.error('❌ JSON parse error from Python:', output, 'Error:', e.message);
            return res.status(500).json({ error: 'Invalid database response', details: output });
        }

        if (result.error) {
            console.error('❌ Python error:', result.error);
            return res.status(500).json({ error: result.error });
        }

        console.log('✅ Booking saved:', result);

        // Store in session for success page
        req.session.successData = {
            quot_id: result.Quotations_id,
            itin_id: result.itineraries_id || '',
            quotation_ref: result.QuotationRef || bookingData.QuotationRef,
            client: bookingData.PrincipalClient,
            is_update: result.is_update || false
        };

        // Write DB IDs back into the Excel file if one was generated
        const excelFile = req.body.excelFile || req.session.excelFile;
        if (excelFile && fs.existsSync(excelFile) && result.Quotations_id) {
            const writeProcess = spawn('python', [
                path.join(__dirname, 'python', 'write_ids_to_excel.py'),
                excelFile,
                String(result.Quotations_id),
                String(result.itineraries_id || '')
            ]);
            writeProcess.stderr.on('data', (data) => {
                console.warn('⚠️  write_ids_to_excel:', data.toString());
            });
            writeProcess.on('close', (writeCode) => {
                if (writeCode === 0) {
                    console.log('✅ IDs written to Excel:', excelFile);
                } else {
                    console.warn('⚠️  write_ids_to_excel exited with code:', writeCode);
                }
                res.redirect('/success');
            });
        } else {
            res.redirect('/success');
        }
    });
});

// -------------------------
// SUCCESS PAGE
// -------------------------
app.get('/success', (req, res) => {
    const successData = req.session.successData || {};
    req.session.successData = null; // clear after use
    
    res.send(
        nunjucks.render('success.html', {
            title: 'Success',
            quot_id: successData.quot_id || '',
            itin_id: successData.itin_id || '',
            quotation_ref: successData.quotation_ref || '',
            client: successData.client || 'Booking',
            is_update: successData.is_update || false,
            has_excel: !!req.session.excelFile
        })
    );
});

// -------------------------
// DOWNLOADS PAGE
// -------------------------
app.get('/downloads', (req, res) => {
    const uploadsDir = path.join(__dirname, 'uploads');
    const bookings = [];

    if (fs.existsSync(uploadsDir)) {
        const bookingFolders = fs.readdirSync(uploadsDir, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory())
            .sort((a, b) => b.name.localeCompare(a.name)); // Sort descending

        bookingFolders.forEach(folder => {
            const folderPath = path.join(uploadsDir, folder.name);
            const files = [];

            try {
                const fileList = fs.readdirSync(folderPath);
                fileList.forEach(file => {
                    const filePath = path.join(folderPath, file);
                    const stats = fs.statSync(filePath);
                    const ext = path.extname(file).toLowerCase().substring(1) || 'file';
                    const size = formatFileSize(stats.size);
                    files.push({
                        name: file,
                        ext: ext,
                        size: size
                    });
                });
            } catch (err) {
                console.error('Error reading folder:', folderPath, err);
            }

            if (files.length > 0) {
                bookings.push({
                    name: folder.name,
                    files: files.sort((a, b) => a.name.localeCompare(b.name))
                });
            }
        });
    }

    res.send(
        nunjucks.render('downloads.html', {
            title: 'Downloads',
            bookings: bookings
        })
    );
});

// Helper function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

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
// DOWNLOAD FILE FROM UPLOADS
// -------------------------
app.get('/download/:booking/:file', (req, res) => {
    const { booking, file } = req.params;
    const filePath = path.join(__dirname, 'uploads', booking, file);
    
    // Security: prevent directory traversal
    const uploadDir = path.join(__dirname, 'uploads', booking);
    const normalizedPath = path.normalize(filePath);
    const normalizedUploadDir = path.normalize(uploadDir);
    
    if (!normalizedPath.startsWith(normalizedUploadDir)) {
        return res.status(403).send('Access denied.');
    }

    if (!fs.existsSync(filePath)) {
        return res.status(404).send('File not found.');
    }

    const fileName = path.basename(filePath);
    res.download(filePath, fileName, (err) => {
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