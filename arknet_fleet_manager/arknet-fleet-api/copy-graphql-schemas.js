const fs = require('fs');
const path = require('path');

function copyGraphQLFiles(src, dest) {
  if (!fs.existsSync(src)) return;
  
  const entries = fs.readdirSync(src, { withFileTypes: true });
  
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    
    if (entry.isDirectory()) {
      copyGraphQLFiles(srcPath, destPath);
    } else if (entry.name.endsWith('.graphql')) {
      if (!fs.existsSync(dest)) {
        fs.mkdirSync(dest, { recursive: true });
      }
      fs.copyFileSync(srcPath, destPath);
      console.log(`Copied: ${srcPath} -> ${destPath}`);
    }
  }
}

const srcDir = path.join(__dirname, 'src', 'extensions', 'graphql');
const destDir = path.join(__dirname, 'dist', 'src', 'extensions', 'graphql');

copyGraphQLFiles(srcDir, destDir);

console.log('Finished copying .graphql schemas to dist directory.');
