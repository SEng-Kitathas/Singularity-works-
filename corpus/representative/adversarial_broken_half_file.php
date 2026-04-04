<?php
if(isset($_GET['go'])) {
  $next = $_GET['next'];
  header("location: " . $next)
  $id = $_GET['id'];
  $query = "SELECT * FROM users WHERE id = '$id'";
