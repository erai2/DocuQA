
export function detectClashes(earthlyBranches) {
  const clashRules = { '子': '午', '午': '子', '卯': '酉', '酉': '卯' };
  return earthlyBranches.map(branch => clashRules[branch] || null);
}
