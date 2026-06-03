import nunjucks from 'nunjucks';
import { templatesDir } from './config.js';

export function configureNunjucks(app) {
    const env = nunjucks.configure(templatesDir, {
        autoescape: true,
        express: app
    });

    env.addFilter('formatDate', (dateStr) => {
        if (!dateStr || typeof dateStr !== 'string') return '';
        const match = dateStr.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
        if (match) {
            return `${match[3]}-${match[2]}-${match[1]}`;
        }
        return dateStr;
    });

    return env;
}

export function render(template, context) {
    return nunjucks.render(template, context);
}
