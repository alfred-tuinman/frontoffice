import { Router } from 'express';
import { listUploadBookings, resolveBookingDir } from '../lib/bookings.js';
import { notesUpload } from '../lib/multer.js';
import { render } from '../lib/nunjucks.js';

export const uploadNotesRouter = Router();

uploadNotesRouter.get('/upload-notes', (req, res) => {
    const messages = req.session.uploadNotesMessages || [];
    req.session.uploadNotesMessages = null;
    const bookings = listUploadBookings();

    res.send(render('upload-notes.html', {
        title: 'Upload Notes',
        bookings: bookings,
        bookingsJson: JSON.stringify(bookings),
        messages: messages
    }));
});

uploadNotesRouter.post('/upload-notes/:booking', (req, res) => {
    if (!resolveBookingDir(req.params.booking)) {
        req.session.uploadNotesMessages = [{
            type: 'error',
            text: 'Invalid booking folder.'
        }];
        return res.redirect('/upload-notes');
    }

    notesUpload.array('files')(req, res, (err) => {
        if (err) {
            console.error('Upload notes error:', err);
            req.session.uploadNotesMessages = [{
                type: 'error',
                text: err.message || 'Upload failed.'
            }];
            return res.redirect('/upload-notes');
        }

        if (!req.files || req.files.length === 0) {
            req.session.uploadNotesMessages = [{
                type: 'error',
                text: 'No files selected.'
            }];
            return res.redirect('/upload-notes');
        }

        const booking = req.params.booking;
        const names = req.files.map((f) => f.filename).join(', ');
        req.session.uploadNotesMessages = [{
            type: 'success',
            text: `Uploaded ${req.files.length} file(s) to ${booking}: ${names}`
        }];
        res.redirect('/upload-notes');
    });
});
