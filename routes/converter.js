import { Router } from 'express';
import path from 'path';
import fs from 'fs';
import crypto from 'crypto';
import { spawn } from 'child_process';
import { pythonExe, pythonDir, uploadsRoot } from '../lib/config.js';
import {
    sanitizeFolderPart,
    buildBookingFolderName
} from '../lib/bookings.js';
import { pdfUpload } from '../lib/multer.js';
import { render } from '../lib/nunjucks.js';

export const converterRouter = Router();

converterRouter.post('/upload', pdfUpload.single('pdf'), (req, res) => {
    console.log('Uploaded file:', req.file);

    if (!req.file) {
        return res.status(400).send('No file uploaded.');
    }

    const tempPdfPath = req.file.path;

    const pythonProcess = spawn(pythonExe, [
        path.join(pythonDir, 'parse_booking.py'),
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

        const quotationRef = sanitizeFolderPart(parsedData.QuotationRef)
            || `booking_${Date.now()}`;
        const folderName = buildBookingFolderName(parsedData);
        const bookingFolder = path.join(uploadsRoot, folderName);

        if (!fs.existsSync(bookingFolder)) {
            fs.mkdirSync(bookingFolder, { recursive: true });
        }

        const pdfFileName = `${quotationRef}.pdf`;
        const pdfPath = path.join(bookingFolder, pdfFileName);
        fs.copyFileSync(tempPdfPath, pdfPath);
        fs.unlinkSync(tempPdfPath);
        console.log('✅ PDF saved:', pdfPath);

        const excelFileName = `${quotationRef}.xlsx`;
        const excelPath = path.join(bookingFolder, excelFileName);

        const excelProcess = spawn(pythonExe, [
            path.join(pythonDir, 'build_excel_wrapper.py'),
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
            }

            req.session.parsed = parsedData;
            req.session.excelFile = excelPath;
            req.session.bookingFolder = bookingFolder;

            const token = crypto.randomBytes(16).toString('hex');
            req.session.formToken = token;

            try {
                const html = render('review.html', {
                    title: 'Review',
                    q: parsedData,
                    excelFile: excelPath,
                    bookingFolder: bookingFolder,
                    token: token
                });
                res.send(html);
            } catch (renderError) {
                console.error('Template render error:', renderError);
                res.status(500).send('Error rendering review page: ' + renderError.message);
            }
        });
    });
});
