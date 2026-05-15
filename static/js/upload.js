if (req.url === '/upload' && req.method === 'POST') {

    res.writeHead(200, {
        'Content-Type': 'text/plain'
    });

    res.end('Upload route works');

    return;
}