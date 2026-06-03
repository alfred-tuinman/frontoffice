import 'dotenv/config';
import express from 'express';
import path from 'path';
import session from 'express-session';
import { PORT, sessionSecret, staticDir } from './lib/config.js';
import { configureNunjucks } from './lib/nunjucks.js';
import { registerRoutes } from './routes/index.js';

const app = express();

app.use(session({
    secret: sessionSecret,
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false }
}));

configureNunjucks(app);

app.use('/static', express.static(staticDir));

app.get('/favicon.ico', (req, res) => {
    res.sendFile(path.join(staticDir, 'favicon.ico'));
});

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

registerRoutes(app);

app.use((req, res) => {
    res.status(404).send('404 Not Found');
});

app.listen(PORT, () => {
    console.log(`http://localhost:${PORT}`);
});
