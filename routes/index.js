import { pagesRouter } from './pages.js';
import { converterRouter } from './converter.js';
import { submitRouter } from './submit.js';
import { downloadsRouter } from './downloads.js';
import { uploadNotesRouter } from './upload-notes.js';

export function registerRoutes(app) {
    app.use(pagesRouter);
    app.use(converterRouter);
    app.use(submitRouter);
    app.use(downloadsRouter);
    app.use(uploadNotesRouter);
}
