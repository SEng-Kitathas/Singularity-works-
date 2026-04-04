<?php
if (isset($_GET['Change'])) {
  $next = $_GET['next'];
  $insert = "UPDATE users SET enabled = 1 WHERE user = 'demo'";
  mysqli_query($GLOBALS["___mysqli_ston"], $insert);
  header("location: " . $next);
}
?>