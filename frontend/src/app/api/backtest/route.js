import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';

const resultsPath = path.join(process.cwd(), 'public', 'backtest_results.json');

// GET: Retorna os dados do arquivo JSON sem cache
export async function GET() {
  try {
    if (!fs.existsSync(resultsPath)) {
      return NextResponse.json({ error: 'Nenhum resultado de backtest encontrado. Rode a simulação primeiro.' }, { status: 404 });
    }
    const fileData = fs.readFileSync(resultsPath, 'utf8');
    const jsonData = JSON.parse(fileData);
    
    const response = NextResponse.json(jsonData);
    response.headers.set('Cache-Control', 'no-store, max-age=0, must-revalidate');
    return response;
  } catch (error) {
    return NextResponse.json({ error: 'Erro ao ler dados do backtest: ' + error.message }, { status: 500 });
  }
}

// POST: Executa o script Python para rodar a simulação e atualizar o JSON
import { verifyAdmin } from '@/lib/adminAuth';

export async function POST(request) {
  // SEC-2: verifyAdmin authentication check
  if (!await verifyAdmin(request)) {
    return NextResponse.json({ error: 'Acesso não autorizado' }, { status: 401 });
  }

  return new Promise((resolve) => {
    const rootDir = path.resolve(process.cwd(), '..');
    const venvPython = path.join(rootDir, 'venv', 'Scripts', 'python.exe');
    const scriptPath = path.join(rootDir, 'backtest_simulator.py');
    
    let command = `python "${scriptPath}"`;
    if (fs.existsSync(venvPython)) {
      command = `"${venvPython}" "${scriptPath}"`;
    }
    
    console.log(`[API Backtest] Executando comando: ${command}`);
    
    // timeout de 120s
    exec(command, { cwd: rootDir, timeout: 120000 }, (error, stdout, stderr) => {
      if (error) {
        console.error(`[API Backtest] Erro de execução: ${error.message}`);
        console.error(`[API Backtest] stderr: ${stderr}`);
        resolve(NextResponse.json({ 
          error: 'Falha ao executar a simulação.', 
          message: 'Erro interno durante processamento do backtest.'
        }, { status: 500 }));
        return;
      }
      
      console.log(`[API Backtest] stdout: ${stdout}`);
      
      try {
        if (!fs.existsSync(resultsPath)) {
          resolve(NextResponse.json({ error: 'Simulação executada, mas o arquivo de resultados não foi gerado.' }, { status: 500 }));
          return;
        }
        const fileData = fs.readFileSync(resultsPath, 'utf8');
        const jsonData = JSON.parse(fileData);
        
        const response = NextResponse.json({
          success: true,
          message: 'Simulação executada e atualizada com sucesso!',
          data: jsonData
        });
        response.headers.set('Cache-Control', 'no-store, max-age=0, must-revalidate');
        resolve(response);
      } catch (readErr) {
        resolve(NextResponse.json({ error: 'Simulação executada, mas erro ao ler os resultados.' }, { status: 500 }));
      }
    });
  });
}
