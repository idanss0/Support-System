const fs = require('fs');
const d = require('docx');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, BorderStyle, LevelFormat, Footer, PageNumber, TableLayoutType } = d;

const [, , src, out] = process.argv;
let lines = fs.readFileSync(src, 'utf8').split('\n')
  .filter(l => !/^<\/?div/.test(l.trim()));

const FONT = { ascii: 'Arial', hAnsi: 'Arial', cs: 'Arial', eastAsia: 'Arial' };
const MONO = { ascii: 'Consolas', hAnsi: 'Consolas', cs: 'Consolas', eastAsia: 'Consolas' };
const ACCENT = '1F4E79';
const PAGE_W = 11906, MARGIN = 1134, CONTENT_W = PAGE_W - 2 * MARGIN;

function runs(text, base = {}) {
  const res = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0, m;
  const push = (t, o = {}) => { if (t) res.push(new TextRun({ text: t, font: FONT, rightToLeft: true, ...base, ...o })); };
  while ((m = re.exec(text))) {
    push(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith('**')) push(tok.slice(2, -2), { bold: true, boldComplexScript: true });
    else res.push(new TextRun({ text: tok.slice(1, -1), font: MONO, size: 18, color: '444444' }));
    last = m.index + tok.length;
  }
  push(text.slice(last));
  return res;
}

const P = (text, opts = {}, runBase = {}) => new Paragraph({
  bidirectional: true, alignment: AlignmentType.START, spacing: { after: 120, line: 276 },
  children: runs(text, runBase), ...opts,
});

function table(rows) {
  const cells = rows.map(r => r.replace(/^\||\|$/g, '').split('|').map(c => c.trim()));
  const header = cells[0];
  const body = cells.slice(2);
  const n = header.length;
  const all = [header, ...body];
  const weight = Array.from({ length: n }, (_, i) =>
    Math.max(7, (header[i] || '').length + 2,
      ...all.map(r => Math.max(0, ...(r[i] || '').replace(/\*\*|`/g, '').split(/\s+/).map(w => w.length + 2))),
      Math.min(60, Math.max(...all.map(r => (r[i] || '').replace(/\*\*|`/g, '').length)))));
  const sum = weight.reduce((a, b) => a + b, 0);
  const widths = weight.map(w => Math.floor(CONTENT_W * w / sum));
  const MIN_COL = 950;
  widths.forEach((w, k) => { if (w < MIN_COL) { widths[k] = MIN_COL; } });
  widths[widths.indexOf(Math.max(...widths))] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const emptyHeader = header.every(h => !h);
  const border = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
  const borders = { top: border, bottom: border, left: border, right: border };
  const mk = (r, isHead) => new TableRow({
    tableHeader: isHead,
    children: Array.from({ length: n }, (_, i) => new TableCell({
      width: { size: widths[i], type: WidthType.DXA }, borders,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      shading: isHead ? { type: ShadingType.CLEAR, fill: 'DCE6F1', color: 'auto' }
        : (i === 0 && emptyHeader ? { type: ShadingType.CLEAR, fill: 'F2F2F2', color: 'auto' } : undefined),
      children: [new Paragraph({ bidirectional: true, spacing: { after: 0 },
        children: runs(r[i] || '', { size: 19, ...(isHead ? { bold: true, boldComplexScript: true } : {}) }) })],
    })),
  });
  const trs = [];
  if (!emptyHeader) trs.push(mk(header, true));
  body.forEach(r => trs.push(mk(r, false)));
  return new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths,
    visuallyRightToLeft: true, layout: TableLayoutType.FIXED, rows: trs });
}

const children = [];
let i = 0;
let numInstance = 0;
while (i < lines.length) {
  const l = lines[i];
  const t = l.trim();
  if (!t) { i++; continue; }
  if (t === '---') { i++; continue; }
  if (t.startsWith('```')) {
    i++;
    const code = [];
    while (i < lines.length && !lines[i].trim().startsWith('```')) code.push(lines[i++]);
    i++;
    code.forEach((c, k) => children.push(new Paragraph({
      bidirectional: false, alignment: AlignmentType.LEFT,
      shading: { type: ShadingType.CLEAR, fill: 'F4F4F4', color: 'auto' },
      spacing: { after: k === code.length - 1 ? 160 : 0, line: 240 },
      children: [new TextRun({ text: c || ' ', font: MONO, size: 16 })],
    })));
    continue;
  }
  let m;
  if ((m = t.match(/^(#{1,3}) (.*)$/))) {
    const lvl = m[1].length;
    const heading = [HeadingLevel.TITLE, HeadingLevel.HEADING_1, HeadingLevel.HEADING_2][lvl - 1];
    children.push(new Paragraph({ heading, bidirectional: true,
      children: runs(m[2].replace(/\*\*/g, '')), pageBreakBefore: lvl === 2 && children.length > 3 && /^(5|8|10|13|16)\./.test(m[2]) }));
    i++; continue;
  }
  if (t.startsWith('|')) {
    const rows = [];
    while (i < lines.length && lines[i].trim().startsWith('|')) rows.push(lines[i++].trim());
    children.push(table(rows));
    children.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
    continue;
  }
  if (t.startsWith('>')) {
    while (i < lines.length && lines[i].trim().startsWith('>')) {
      const q = lines[i].trim().replace(/^>\s?/, '');
      if (q) children.push(P(q, {
        shading: { type: ShadingType.CLEAR, fill: 'FFF4E5', color: 'auto' },
        border: { right: { style: BorderStyle.SINGLE, size: 18, color: 'E69500', space: 6 } },
        indent: { start: 200 },
      }, { size: 20 }));
      i++;
    }
    continue;
  }
  if ((m = l.match(/^(\s*)- (.*)$/))) {
    children.push(P(m[2], { numbering: { reference: 'bullets', level: m[1].length >= 2 ? 1 : 0 }, spacing: { after: 60 } }));
    i++; continue;
  }
  if ((m = l.match(/^(\s*)(\d+)\. (.*)$/))) {
    children.push(P(m[3], { numbering: { reference: 'numbers', level: 0, instance: numInstance }, spacing: { after: 60 } }));
    i++;
    if (!(lines[i] || '').match(/^\s*\d+\. /) && !(lines[i] || '').match(/^\s+- /)) numInstance++;
    continue;
  }
  children.push(P(t));
  i++;
}


const doc = new Document({
  creator: 'Support Technical Management',
  title: 'MVP - Support Control Tower',
  styles: {
    default: { document: { run: { font: FONT, size: 21, sizeComplexScript: 21 } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal',
        run: { size: 40, sizeComplexScript: 40, bold: true, boldComplexScript: true, color: ACCENT, font: FONT },
        paragraph: { spacing: { after: 240 } } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, sizeComplexScript: 30, bold: true, boldComplexScript: true, color: ACCENT, font: FONT },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 4 } } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 25, sizeComplexScript: 25, bold: true, boldComplexScript: true, color: '2E75B6', font: FONT },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: 'bullets', levels: [
      { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.START,
        style: { paragraph: { indent: { start: 540, hanging: 270 } } } },
      { level: 1, format: LevelFormat.BULLET, text: '◦', alignment: AlignmentType.START,
        style: { paragraph: { indent: { start: 1080, hanging: 270 } } } } ] },
    { reference: 'numbers', levels: [
      { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.START,
        style: { paragraph: { indent: { start: 540, hanging: 360 } } } } ] },
  ] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 },
      margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT, ' / ', PageNumber.TOTAL_PAGES], size: 18, color: '808080' })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log('written', out); });
