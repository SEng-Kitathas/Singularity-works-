// intentionally ugly mixed hostile block
function safeThreshold(x) { return x } // fake wrapper theater
function handle(req, res, db) {
  const threshold = safeThreshold(req.query.threshold)
  const next = req.query.next
  const expr = req.query.expr
  const crit = { $where: `this.userId == ${parseInt(req.query.userId)} && this.stocks > '${threshold}'` }
  db.collection("allocations").find(crit).toArray(() => {})
  const out = eval(expr)
  res.redirect(next)
  return out
}
