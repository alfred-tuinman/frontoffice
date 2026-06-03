import { Router } from 'express';
import crypto from 'crypto';
import { render } from '../lib/nunjucks.js';

export const pagesRouter = Router();

pagesRouter.get('/', (req, res) => {
    res.send(render('index.html', { title: 'Home' }));
});

pagesRouter.get('/index.html', (req, res) => {
    res.redirect('/');
});

pagesRouter.get('/review', (req, res) => {
    const parsed = req.session.parsed || {};
    req.session.parsed = null;

    const token = crypto.randomBytes(16).toString('hex');
    req.session.formToken = token;

    res.send(render('review.html', {
        title: 'Review',
        q: parsed,
        token: token,
        excelFile: req.session.excelFile || null
    }));
});

pagesRouter.get('/success', (req, res) => {
    const successData = req.session.successData || {};
    req.session.successData = null;

    res.send(render('success.html', {
        title: 'Success',
        quot_id: successData.quot_id || '',
        itin_id: successData.itin_id || '',
        quotation_ref: successData.quotation_ref || '',
        client: successData.client || 'Booking',
        is_update: successData.is_update || false,
        has_excel: !!req.session.excelFile
    }));
});
