
export function analyzeFortune(stems, branches) {
  const strength = stems.filter(s => ['甲', '乙'].includes(s)).length;
  let interpretation = strength > 2 ? "세다" : "약하다";
  return {
    strength,
    interpretation,
    tips: interpretation === "세다" ? "제압 필요" : "보완 필요"
  };
}
