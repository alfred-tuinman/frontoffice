import http from 'http';
import fs from 'fs';
import path from 'path';
import nunjucks from 'nunjucks';
import { fileURLToPath } from 'url';

const PORT = 3010;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

nunjucks.configure('templates', {
    autoescape: true
});

// your routes
const routes = {
    '/': 'index.html',
    '/index.html': 'index.html',
    '/review': 'review.html',
    '/success': 'success.html'
};

http.createServer((req, res) => {

    // -------------------------
    // 1. STATIC FILES
    // -------------------------
    if (req.url.startsWith('/static/')) {

        const filePath = path.join(__dirname, req.url);

        fs.readFile(filePath, (err, data) => {
            if (err) {
                res.writeHead(404);
                res.end('File not found');
                return;
            }

            const ext = path.extname(filePath);

            const mime = {
                '.js': 'text/javascript',
                '.css': 'text/css',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.svg': 'image/svg+xml'
            };

            res.writeHead(200, {
                'Content-Type': mime[ext] || 'text/plain'
            });

            res.end(data);
        });

        return;
    }

    // -------------------------
    // 2. HTML ROUTES
    // -------------------------
    const template = routes[req.url];

    if (!template) {
        res.writeHead(404);
        res.end('404 Not Found');
        return;
    }

    const html = nunjucks.render(template, {
        title: 'My Site'
    });

    res.writeHead(200, {
        'Content-Type': 'text/html'
    });

    res.end(html);

}).listen(PORT, () => {
    console.log(`http://localhost:${PORT}`);
});