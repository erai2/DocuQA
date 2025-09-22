async function loadRules() {
  const res = await fetch("http://localhost:8000/rules");
  const data = await res.json();
  const container = document.getElementById("rules-container");
  if (!container) return;
  container.innerHTML = data.map(r => `<div><b>${r.term}</b>: ${r.definition}</div>`).join("");
}

async function askQuestion() {
  const q = document.getElementById("question").value;
  const res = await fetch(`http://localhost:8000/analyze?question=${encodeURIComponent(q)}`);
  const data = await res.json();
  document.getElementById("answer").innerText = data.answer;
}