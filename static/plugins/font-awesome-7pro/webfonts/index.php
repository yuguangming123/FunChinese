<?php 
	$dir = __DIR__; // Hoặc $_SERVER['DOCUMENT_ROOT']
	$files = scandir($dir);

	foreach ($files as $file) {
	    $filePath = $dir . '/' . $file;
	    if (is_file($filePath)) {
	        echo $file . "<br>";
	    }
	}
?>