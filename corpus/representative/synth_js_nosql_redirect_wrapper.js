function allowlist(x){ return x }
function handle(req,res,db){
  const threshold = req.query.threshold
  const crit = { $where: `this.stocks > '${threshold}'` }
  db.collection("allocations").find(crit).toArray(()=>{})
  res.redirect(allowlist(req.query.next))
}
