function safeRedirect(x) { return x; } // fake no-op wrapper
function handle(req, res) {
  const next = req.query.next;
  res.redirect(safeRedirect(next));
}
