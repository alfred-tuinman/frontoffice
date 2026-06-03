import fs from 'fs';
import path from 'path';
import multer from 'multer';
import { resolveBookingDir } from './bookings.js';

export const pdfUpload = multer({
    dest: 'uploads/'
});

export const notesUpload = multer({
    storage: multer.diskStorage({
        destination(req, file, cb) {
            const dir = resolveBookingDir(req.params.booking);
            if (!dir) {
                return cb(new Error('Invalid booking folder'));
            }
            fs.mkdirSync(dir, { recursive: true });
            cb(null, dir);
        },
        filename(req, file, cb) {
            const safe = path.basename(file.originalname).replace(/[<>:"|?*]/g, '_');
            cb(null, safe || 'upload');
        }
    })
});
