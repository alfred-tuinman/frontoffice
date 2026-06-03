import { Router } from 'express';
import path from 'path';
import fs from 'fs';
import { spawn } from 'child_process';
import { pythonExe, pythonDir } from '../lib/config.js';

export const submitRouter = Router();

submitRouter.post('/submit/:token', (req, res) => {
    console.log('📝 Form submitted with token:', req.params.token);

    const bookingData = {
        ...req.body,
        QuotationDate: new Date().toISOString().split('T')[0]
    };

    const pythonProcess = spawn(pythonExe, [
        path.join(pythonDir, 'save_booking.py'),
        JSON.stringify(bookingData)
    ]);

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.error('❌ Database save error:', errorOutput);
            return res.status(500).json({
                error: 'Error saving booking to database',
                details: errorOutput
            });
        }

        let result;
        try {
            result = JSON.parse(output);
        } catch (e) {
            console.error('❌ JSON parse error from Python:', output);
            return res.status(500).json({
                error: 'Invalid database response',
                details: output
            });
        }

        if (result.error) {
            return res.status(500).json({ error: result.error });
        }

        console.log('✅ Booking saved:', result);

        req.session.successData = {
            quot_id: result.Quotations_id,
            itin_id: result.itineraries_id || '',
            quotation_ref: result.QuotationRef || bookingData.QuotationRef,
            client: bookingData.PrincipalClient,
            is_update: result.is_update || false
        };

        const excelFile = req.body.excelFile || req.session.excelFile;
        if (excelFile && fs.existsSync(excelFile) && result.Quotations_id) {
            const writeProcess = spawn(pythonExe, [
                path.join(pythonDir, 'write_ids_to_excel.py'),
                excelFile,
                String(result.Quotations_id),
                String(result.itineraries_id || '')
            ]);
            writeProcess.stderr.on('data', (data) => {
                console.warn('⚠️  write_ids_to_excel:', data.toString());
            });
            writeProcess.on('close', () => {
                res.redirect('/success');
            });
        } else {
            res.redirect('/success');
        }
    });
});
