import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const rootDir = path.join(__dirname, '..');
export const uploadsRoot = path.join(rootDir, 'uploads');
export const staticDir = path.join(rootDir, 'static');
export const templatesDir = path.join(rootDir, 'templates');
export const pythonDir = path.join(rootDir, 'python');

export const PORT = Number(process.env.PORT) || 3010;

export const pythonExe =
    process.env.PYTHON_EXE
    || 'C:\\Users\\sw\\AppData\\Local\\Programs\\Python\\Python314\\python.exe';

export const sessionSecret = process.env.SESSION_SECRET || 'booking_secret';
