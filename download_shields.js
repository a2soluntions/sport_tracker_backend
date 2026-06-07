const fs = require('fs');
const https = require('https');
const path = require('path');

const TEAM_LOGOS = {
    'São Paulo': 'https://upload.wikimedia.org/wikipedia/commons/4/4b/S%C3%A3o_Paulo_Futebol_Clube.svg',
    'Botafogo': 'https://upload.wikimedia.org/wikipedia/commons/c/c2/Botafogo_de_Futebol_e_Regatas_logo.svg',
    'Vitória': 'https://upload.wikimedia.org/wikipedia/pt/2/25/Esporte_Clube_Vit%C3%B3ria_logo.svg',
    'Internacional': 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Escudo_do_Sport_Club_Internacional.svg',
    'Mirassol': 'https://upload.wikimedia.org/wikipedia/pt/1/1a/Mirassol_FC.svg',
    'Fluminense': 'https://upload.wikimedia.org/wikipedia/commons/a/a3/Escudo_do_Fluminense.svg',
    'Grêmio': 'https://upload.wikimedia.org/wikipedia/commons/4/4e/Gr%C3%AAmio_Foot-Ball_Porto_Alegrense.svg',
    'Santos': 'https://upload.wikimedia.org/wikipedia/commons/3/35/Santos_logo.svg',
    'Flamengo': 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg',
    'Palmeiras': 'https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg',
    'Cruzeiro': 'https://upload.wikimedia.org/wikipedia/commons/9/90/Cruzeiro_Esporte_Clube_%28logo%29.svg',
    'Chapecoense': 'https://upload.wikimedia.org/wikipedia/commons/e/ec/Associa%C3%A7%C3%A3o_Chapecoense_de_Futebol_-_2018.svg',
    'Remo': 'https://upload.wikimedia.org/wikipedia/commons/4/47/Clube_do_Remo_%28escudo%29.svg',
    'Athletico-PR': 'https://upload.wikimedia.org/wikipedia/commons/b/b3/CA_Paranaense.svg',
    'Corinthians': 'https://upload.wikimedia.org/wikipedia/pt/b/b4/Corinthians_simbolo.png',
    'Atlético-MG': 'https://upload.wikimedia.org/wikipedia/commons/5/5f/Atletico_mineiro_galo.png',
    'Vasco': 'https://upload.wikimedia.org/wikipedia/pt/a/ac/CRVascodaGama.png',
    'Red Bull Bragantino': 'https://upload.wikimedia.org/wikipedia/pt/9/94/Red_Bull_Bragantino_v2.png',
    'Coritiba': 'https://upload.wikimedia.org/wikipedia/commons/b/b3/Coritiba_FBC_%282011%29.svg',
    'Bahia': 'https://upload.wikimedia.org/wikipedia/pt/9/90/Esporte_Clube_Bahia_logo.png'
};

const sanitize = (name) => name.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '-');

fs.mkdirSync('frontend/public/shields', { recursive: true });

async function downloadAll() {
  for (const [name, url] of Object.entries(TEAM_LOGOS)) {
    const ext = url.endsWith('.svg') ? '.svg' : '.png';
    const filename = sanitize(name) + ext;
    const dest = path.join('frontend', 'public', 'shields', filename);
    await new Promise((resolve) => {
      https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' } }, (res) => {
        if (res.statusCode === 200) {
          const file = fs.createWriteStream(dest);
          res.pipe(file);
          file.on('finish', () => resolve());
        } else if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          https.get(res.headers.location, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res2) => {
             const file2 = fs.createWriteStream(dest);
             res2.pipe(file2);
             file2.on('finish', () => resolve());
          });
        } else {
          console.log('Failed', name, res.statusCode);
          resolve();
        }
      }).on('error', () => resolve());
    });
    console.log('Downloaded:', filename);
  }
}

downloadAll().then(() => console.log('Done!'));
