import "dotenv/config";
import express from 'express';
import path from 'path';
import nunjucks from 'nunjucks';
import multer from 'multer';
import { fileURLToPath } from 'url';

const PORT = 3010;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// -------------------------
// NUNJUCKS
// -------------------------
nunjucks.configure('templates', {
    autoescape: true,
    express: app
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

    res.send(
        nunjucks.render('review.html', {
            title: 'Review'
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

    // later:
    // parse PDF
    // extract booking info
    // save to database

    res.redirect('/review');
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