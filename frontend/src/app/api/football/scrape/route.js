import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { verifyAdmin } from '@/lib/adminAuth';

export async function POST(request) {
  // SEC-2: verifyAdmin authentication check
  if (!await verifyAdmin(request)) {
    return NextResponse.json({ error: 'Acesso não autorizado' }, { status: 401 });
  }

  return new Promise((resolve) => {
    const rootDir = path.resolve(process.cwd(), '..');
    const venvPython = path.join(rootDir, 'venv', 'Scripts', 'python.exe');
    const scriptPath = path.join(rootDir, 'main.py');
    
    let command = `python "${scriptPath}"`;
    if (fs.existsSync(venvPython)) {
      command = `"${venvPython}" "${scriptPath}"`;
    }
    
    console.log(`[API Scraper] Executando comando: ${command}`);
    
    // PERF-1: timeout de 120000ms (2 minutos)
    exec(command, { cwd: rootDir, timeout: 120000 }, (error, stdout, stderr) => {
      if (error) {
        console.error(`[API Scraper] Erro de execução: ${error.message}`);
        console.error(`[API Scraper] stderr: ${stderr}`);
        
        // PERF-2: Safe error message, do not leak internal path/stderr details to the frontend
        resolve(NextResponse.json({ 
          error: 'Falha ao executar o Scraper.',
          message: 'Erro interno ao processar dados esportivos.'
        }, { status: 500 }));
        return;
      }
      
      console.log(`[API Scraper] stdout: ${stdout}`);
      
      resolve(NextResponse.json({
        success: true,
        message: 'Ciclo do Scraper e Análise +EV finalizado com sucesso!'
      }));
    });
  });
}

