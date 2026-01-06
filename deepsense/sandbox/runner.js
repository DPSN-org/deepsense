const { execSync } = require('child_process');
const fs = require('fs');

const meta = JSON.parse(fs.readFileSync('script/meta.json'));
const code = meta.code || '';
const packages = meta.requirements || [];

// Install npm packages with suppressed warnings
if (packages.length > 0) {
  try {
    execSync(`npm install --silent --no-audit --no-fund ${packages.join(' ')}`, { 
      stdio: 'pipe',
      encoding: 'utf-8'
    });
  } catch (err) {
    console.error('NPM install failed:', err.message);
  }
}

// Write code to file
fs.writeFileSync('script/user_script.js', code);

// Execute code
try {
  const output = execSync('node script/user_script.js', { encoding: 'utf-8' });
  console.log(output);
} catch (err) {
  console.error('Execution error:', err.stderr || err.message);
}

