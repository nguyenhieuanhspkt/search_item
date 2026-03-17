export const tableStyles = {
  // Khung ngoài cùng phải có border
  wrapper:
    "border border-slate-300 rounded-2xl overflow-hidden bg-white shadow-xl",
  scrollArea: "max-h-[500px] overflow-y-auto",

  table: "w-full text-sm border-collapse border-spacing-0",
  // Header có nền xám và gạch dưới đậm
  thead: "bg-slate-100 border-b-2 border-slate-300 sticky top-0 z-10",
  th: "p-4 text-slate-700 font-bold text-xs uppercase tracking-wider text-left border-r border-slate-200 last:border-r-0",

  // Dòng: Quan trọng nhất là divide-x và border-b
  tr: "hover:bg-blue-50/50 transition-colors border-b border-slate-200",
  // Các ô (Cell) phải có border-r (border bên phải) để tạo đường kẻ dọc
  tdStt:
    "p-4 text-center text-slate-400 font-mono text-xs bg-slate-50 border-r border-slate-200 w-14",
  tdMain:
    "p-4 font-semibold text-slate-800 text-[13px] leading-snug border-r border-slate-200",
  tdSub:
    "p-4 text-slate-500 text-[12px] leading-relaxed border-r border-slate-200",
  tdUnit:
    "p-4 text-center text-slate-700 text-xs font-bold uppercase w-24 bg-slate-50/30",

  // Nút bấm giữ nguyên
  btnConfirm:
    "flex-1 bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-black shadow-lg shadow-blue-200 flex items-center justify-center gap-2.5 transition-all hover:scale-[1.01] active:scale-[0.99]",
  btnCancel:
    "px-8 border-2 border-red-100 text-red-600 rounded-xl hover:bg-red-50 font-semibold transition-colors",
};
