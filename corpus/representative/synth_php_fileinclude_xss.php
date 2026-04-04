<?php
$page = $_GET['page'];
$name = $_GET['name'];
include($page);
$html .= "<div>Hello " . $name . "</div>";
?>