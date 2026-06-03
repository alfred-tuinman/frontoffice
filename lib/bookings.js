import fs from 'fs';
import path from 'path';
import { uploadsRoot } from './config.js';

export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export function sanitizeFolderPart(value) {
    if (!value || typeof value !== 'string') {
        return '';
    }
    return value
        .trim()
        .replace(/['']/g, '')
        .replace(/[<>:"|?*\\/]/g, '')
        .replace(/\s+/g, '_')
        .replace(/[^a-zA-Z0-9_-]/g, '')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '')
        .slice(0, 48);
}

export function extractClientSurname(parsedData) {
    const fromPax = sanitizeFolderPart(parsedData.PaxName);
    if (fromPax) {
        return fromPax;
    }
    const client = parsedData.PrincipalClient;
    if (client && typeof client === 'string') {
        const parts = client.trim().split(/\s+/).filter(Boolean);
        if (parts.length > 0) {
            return sanitizeFolderPart(parts[parts.length - 1]);
        }
    }
    return '';
}

export function buildBookingFolderName(parsedData) {
    const quotationRef = sanitizeFolderPart(parsedData.QuotationRef)
        || `booking_${Date.now()}`;
    const surname = extractClientSurname(parsedData);
    if (surname) {
        return `${surname}_${quotationRef}`;
    }
    return quotationRef;
}

export function resolveBookingDir(booking) {
    if (!booking || typeof booking !== 'string' || !/^[a-zA-Z0-9_-]+$/.test(booking)) {
        return null;
    }
    const dir = path.join(uploadsRoot, booking);
    const normalized = path.normalize(dir);
    const root = path.normalize(uploadsRoot);
    if (normalized !== root && !normalized.startsWith(root + path.sep)) {
        return null;
    }
    return normalized;
}

export function listUploadBookings() {
    const bookings = [];

    if (!fs.existsSync(uploadsRoot)) {
        return bookings;
    }

    const bookingFolders = fs.readdirSync(uploadsRoot, { withFileTypes: true })
        .filter((dirent) => dirent.isDirectory())
        .sort((a, b) => b.name.localeCompare(a.name));

    bookingFolders.forEach((folder) => {
        const folderPath = path.join(uploadsRoot, folder.name);
        const files = [];

        try {
            fs.readdirSync(folderPath).forEach((file) => {
                const filePath = path.join(folderPath, file);
                const stats = fs.statSync(filePath);
                if (!stats.isFile()) {
                    return;
                }
                const ext = path.extname(file).toLowerCase().substring(1) || 'file';
                files.push({
                    name: file,
                    ext: ext,
                    size: formatFileSize(stats.size)
                });
            });
        } catch (err) {
            console.error('Error reading folder:', folderPath, err);
        }

        bookings.push({
            name: folder.name,
            files: files.sort((a, b) => a.name.localeCompare(b.name))
        });
    });

    return bookings;
}
