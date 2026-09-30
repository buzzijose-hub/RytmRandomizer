/** Original 5 × 7 appliance glyphs. No font or firmware assets are imported.
 * Rebuild: node fonts/build-pixel-font.mjs (from desktop/web).
 * TrueType layout: https://learn.microsoft.com/en-us/typography/opentype/spec/otff
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const pixels = {
  ' ': '00000/00000/00000/00000/00000/00000/00000',
  A: '01110/10001/10001/11111/10001/10001/10001',
  B: '11110/10001/10001/11110/10001/10001/11110',
  C: '01111/10000/10000/10000/10000/10000/01111',
  D: '11110/10001/10001/10001/10001/10001/11110',
  E: '11111/10000/10000/11110/10000/10000/11111',
  F: '11111/10000/10000/11110/10000/10000/10000',
  G: '01111/10000/10000/10111/10001/10001/01110',
  H: '10001/10001/10001/11111/10001/10001/10001',
  I: '11111/00100/00100/00100/00100/00100/11111',
  J: '00111/00010/00010/00010/00010/10010/01100',
  K: '10001/10010/10100/11000/10100/10010/10001',
  L: '10000/10000/10000/10000/10000/10000/11111',
  M: '10001/11011/10101/10101/10001/10001/10001',
  N: '10001/11001/10101/10011/10001/10001/10001',
  O: '01110/10001/10001/10001/10001/10001/01110',
  P: '11110/10001/10001/11110/10000/10000/10000',
  Q: '01110/10001/10001/10001/10101/10010/01101',
  R: '11110/10001/10001/11110/10100/10010/10001',
  S: '01111/10000/10000/01110/00001/00001/11110',
  T: '11111/00100/00100/00100/00100/00100/00100',
  U: '10001/10001/10001/10001/10001/10001/01110',
  V: '10001/10001/10001/10001/10001/01010/00100',
  W: '10001/10001/10001/10101/10101/10101/01010',
  X: '10001/10001/01010/00100/01010/10001/10001',
  Y: '10001/10001/01010/00100/00100/00100/00100',
  Z: '11111/00001/00010/00100/01000/10000/11111',
  '0': '01110/10001/10011/10101/11001/10001/01110',
  '1': '00100/01100/00100/00100/00100/00100/01110',
  '2': '01110/10001/00001/00010/00100/01000/11111',
  '3': '11110/00001/00001/01110/00001/00001/11110',
  '4': '00010/00110/01010/10010/11111/00010/00010',
  '5': '11111/10000/10000/11110/00001/00001/11110',
  '6': '01110/10000/10000/11110/10001/10001/01110',
  '7': '11111/00001/00010/00100/01000/01000/01000',
  '8': '01110/10001/10001/01110/10001/10001/01110',
  '9': '01110/10001/10001/01111/00001/00001/01110',
  '.': '00000/00000/00000/00000/00000/00110/00110',
  ',': '00000/00000/00000/00000/00110/00110/00100',
  ':': '00000/00110/00110/00000/00110/00110/00000',
  ';': '00000/00110/00110/00000/00110/00110/00100',
  '-': '00000/00000/00000/11111/00000/00000/00000',
  '_': '00000/00000/00000/00000/00000/00000/11111',
  '+': '00000/00100/00100/11111/00100/00100/00000',
  '/': '00001/00001/00010/00100/01000/10000/10000',
  '=': '00000/00000/11111/00000/11111/00000/00000',
  '%': '11001/11010/00010/00100/01000/01011/10011',
  '!': '00100/00100/00100/00100/00100/00000/00100',
  '?': '01110/10001/00001/00010/00100/00000/00100',
  '#': '01010/01010/11111/01010/11111/01010/01010',
  '(': '00010/00100/01000/01000/01000/00100/00010',
  ')': '01000/00100/00010/00010/00010/00100/01000',
  '[': '01110/01000/01000/01000/01000/01000/01110',
  ']': '01110/00010/00010/00010/00010/00010/01110',
  '<': '00001/00010/00100/01000/00100/00010/00001',
  '>': '10000/01000/00100/00010/00100/01000/10000',
  '|': '00100/00100/00100/00100/00100/00100/00100',
  "'": '00100/00100/00000/00000/00000/00000/00000',
  '"': '01010/01010/00000/00000/00000/00000/00000',
  '*': '00000/10101/01110/11111/01110/10101/00000',
};

function words(values) {
  const bytes = Buffer.alloc(values.length * 2);
  values.forEach((v, i) => bytes.writeUInt16BE(v & 0xffff, i * 2));
  return bytes;
}
function longs(values) {
  const bytes = Buffer.alloc(values.length * 4);
  values.forEach((v, i) => bytes.writeUInt32BE(v >>> 0, i * 4));
  return bytes;
}
function padded(bytes) {
  return Buffer.concat([bytes, Buffer.alloc((4 - (bytes.length % 4)) % 4)]);
}
function checksum(bytes) {
  const aligned = padded(bytes);
  let result = 0;
  for (let i = 0; i < aligned.length; i += 4) result = (result + aligned.readUInt32BE(i)) >>> 0;
  return result;
}
function glyph(bitmap) {
  const contours = [];
  bitmap.split('/').forEach((row, y) => [...row].forEach((bit, x) => {
    if (bit === '1') {
      const xx = x * 100 + 50;
      const yy = (6 - y) * 100;
      contours.push([[xx, yy], [xx, yy + 100], [xx + 100, yy + 100], [xx + 100, yy]]);
    }
  }));
  const points = contours.flat();
  let previousX = 0;
  let previousY = 0;
  const xDeltas = points.map(([x]) => { const d = x - previousX; previousX = x; return d; });
  const yDeltas = points.map(([, y]) => { const d = y - previousY; previousY = y; return d; });
  return padded(Buffer.concat([
    words([contours.length, 0, 0, 550, 700]),
    words(contours.map((_, i) => i * 4 + 3)), words([0]),
    Buffer.alloc(points.length, 1), words(xDeltas), words(yDeltas),
  ]));
}

const characters = Array.from({ length: 95 }, (_, i) => String.fromCharCode(i + 32));
const glyphs = [glyph(pixels['?']), ...characters.map((c) => glyph(pixels[c.toUpperCase()] ?? pixels['?']))];
const offsets = [0];
for (const bytes of glyphs) offsets.push(offsets.at(-1) + bytes.length);
const head = Buffer.concat([longs([0x10000, 0x10000, 0, 0x5f0f3cf5]), words([3, 1000]), Buffer.alloc(16), words([0, 0, 550, 700, 0, 8, 2, 1, 0])]);
const hhea = Buffer.concat([longs([0x10000]), words([800, -200, 0, 600, 0, 50, 550, 1, 0, 0, 0, 0, 0, 0, 0, glyphs.length])]);
const maxp = Buffer.concat([longs([0x10000]), words([glyphs.length, 140, 35, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0])]);
const cmapSubtable = words([4, 32, 0, 4, 4, 1, 0, 126, 0xffff, 0, 32, 0xffff, -31, 1, 0, 0]);
const cmap = Buffer.concat([words([0, 1, 3, 1]), longs([12]), cmapSubtable]);
const names = [
  [0, 'Copyright 2026 RytmRandomizer contributors. MIT license. Original glyphs.'],
  [1, 'Rytm Appliance Pixel'], [2, 'Regular'], [3, 'RytmAppliancePixel-1.0'],
  [4, 'Rytm Appliance Pixel'], [5, 'Version 1.0'], [6, 'RytmAppliancePixel'],
];
const strings = names.map(([, label]) => Buffer.from(label, 'utf16le').swap16());
let stringOffset = 0;
const nameRecords = names.map(([id], index) => {
  const record = words([3, 1, 0x409, id, strings[index].length, stringOffset]);
  stringOffset += strings[index].length;
  return record;
});
const name = Buffer.concat([words([0, names.length, 6 + names.length * 12]), ...nameRecords, ...strings]);
const os2 = Buffer.alloc(78);
words([0, 600, 400, 5, 0, 650, 600, 0, 75, 650, 600, 0, 350, 50, 250, 0]).copy(os2);
os2.writeUInt32BE(1, 42);
os2.write('RYTM', 58);
words([0x40, 32, 126, 800, -200, 0, 800, 200]).copy(os2, 62);
const tables = {
  'OS/2': os2, cmap, glyf: Buffer.concat(glyphs), head, hhea,
  hmtx: words(glyphs.flatMap(() => [600, 0])), loca: longs(offsets), maxp, name,
  post: Buffer.concat([longs([0x30000, 0]), words([-100, 50]), longs([1, 0, 0, 0, 0])]),
};
const tags = Object.keys(tables).sort();
const count = tags.length;
const power = 2 ** Math.floor(Math.log2(count));
let offset = 12 + count * 16;
let headOffset = 0;
const records = tags.map((tag) => {
  const bytes = tables[tag];
  if (tag === 'head') headOffset = offset;
  const record = Buffer.concat([Buffer.from(tag), longs([checksum(bytes), offset, bytes.length])]);
  offset += padded(bytes).length;
  return record;
});
const font = Buffer.concat([
  longs([0x10000]), words([count, power * 16, Math.log2(power), count * 16 - power * 16]),
  ...records, ...tags.map((tag) => padded(tables[tag])),
]);
font.writeUInt32BE((0xb1b0afba - checksum(font)) >>> 0, headOffset + 8);
const output = fileURLToPath(new URL('../src/appliance/assets/appliance-pixel.ttf', import.meta.url));
mkdirSync(fileURLToPath(new URL('../src/appliance/assets/', import.meta.url)), { recursive: true });
writeFileSync(output, font);
console.log(`Wrote original appliance pixel font (${font.length} bytes, ${glyphs.length} glyphs).`);
