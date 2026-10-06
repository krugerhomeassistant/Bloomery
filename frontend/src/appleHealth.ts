/** Stream Apple Health's export.xml (often 100s of MB) in the browser and keep only cycle-related records.
 *  Output is what /api/import/other expects: {format: 'apple_health', records: [type, date, value, unit][]} */
const TYPES = new Set([
  'MenstrualFlow', 'IntermenstrualBleeding', 'CervicalMucusQuality', 'OvulationTestResult', 'PregnancyTestResult',
  'BasalBodyTemperature', 'AppleSleepingWristTemperature', 'AbdominalCramps', 'Bloating', 'BreastPain', 'Headache', 'Acne', 'LowerBackPain', 'Fatigue',
  'Nausea', 'MoodChanges', 'SleepChanges', 'HotFlashes', 'Dizziness', 'Constipation', 'Diarrhea', 'AppetiteChanges', 'PelvicPain',
])
const attr = (tag: string, name: string) => tag.match(new RegExp(`\\b${name}="([^"]*)"`))?.[1] ?? ''

export async function extractAppleHealth(file: File, onProgress?: (pct: number) => void) {
  const records: [string, string, string, string][] = []
  const reader = file.stream().pipeThrough(new TextDecoderStream()).getReader()
  let buf = '', seen = 0
  const scan = (text: string) => {
    for (const m of text.matchAll(/<Record\b[^>]*>/g)) {
      const type = attr(m[0], 'type').replace(/^HK(Category|Quantity)TypeIdentifier/, '')
      // wrist temperature is measured overnight: file it under the morning it ends (like a waking basal reading)
      if (TYPES.has(type)) records.push([type, attr(m[0], type === 'AppleSleepingWristTemperature' ? 'endDate' : 'startDate').slice(0, 10), attr(m[0], 'value'), attr(m[0], 'unit')])
    }
  }
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    seen += value.length
    buf += value
    const cut = buf.lastIndexOf('<') // everything before the last '<' contains only complete tags
    scan(buf.slice(0, cut))
    buf = buf.slice(cut)
    onProgress?.(Math.min(99, Math.round((seen / file.size) * 100)))
  }
  scan(buf)
  return { format: 'apple_health', records }
}
