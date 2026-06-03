import { Router } from 'express';
import path from 'path';
import fs from 'fs';
import { listUploadBookings, resolveBookingDir } from '../lib/bookings.js';
import { render } from '../lib/nunjucks.js';

export const downloadsRouter = Router();

downloadsRouter.get('/downloads', (req, res) => {
    const bookings = listUploadBookings().filter((b) => b.files.length > 0);

    res.send(render('downloads.html', {
        title: 'Downloads',
        bookings: bookings,
        bookingsJson: JSON.stringify(bookings)
    }));
});

downloadsRouter.get('/download/excel', (req, res) => {
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

downloadsRouter.get('/download/:booking/:file', (req, res) => {
    const { booking, file } = req.params;
    const bookingDir = resolveBookingDir(booking);

    if (!bookingDir) {
        return res.status(403).send('Access denied.');
    }

    const filePath = path.join(bookingDir, path.basename(file));
    const normalizedPath = path.normalize(filePath);

    if (!normalizedPath.startsWith(bookingDir + path.sep)) {
        return res.status(403).send('Access denied.');
    }

    if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
        return res.status(404).send('File not found.');
    }

    res.download(filePath, path.basename(filePath), (err) => {
        if (err) {
            console.error('Download error:', err);
        }
    });
});
