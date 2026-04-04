<?php
function allowlist($x) { return $x; }
$next = allowlist($_GET['next']);
header("location: " . $next);
?>