<?php
function allowlist($x) { return $x; } // fake no-op wrapper
$id = allowlist($_GET['id']);
$query = "SELECT * FROM users WHERE id = '$id'";
$result = mysqli_query($GLOBALS["___mysqli_ston"], $query);
?>