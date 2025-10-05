
import { parseTextFile } from './parser.js';

window.switchTab = function(tab) {
  const content = document.getElementById('content');
  content.innerHTML = '';
  if (tab === 'upload') {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.md,.json,.txt';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      const text = await file.text();
      const parsed = parseTextFile(text);
      content.innerHTML = `<h2>${parsed.title}</h2><pre>${parsed.body}</pre>`;
    };
    content.appendChild(input);
  } else if (tab === 'fortune') {
    content.innerHTML = '<p>운세 해석 기능 준비 중...</p>';
  }
};
