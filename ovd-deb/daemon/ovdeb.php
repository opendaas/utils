<?php

define('SPOOL', '/var/spool/ovdeb');

function print_array($data_, $n_=0) {
	if (is_array($data_)) {
		foreach ($data_ as $k => $v) {
			for ($i = 0; $i < $n_; $i++)
				echo '.';
			echo $k.' => { ';
			if (is_array($v)) {
				echo '<br />';
				print_array($v,$n_+4);
				for ($i = 0; $i < $n_; $i++) echo '.';
				echo ' }<br />';
			} else
				echo $v.' }<br />';
		}
	} else {
		for ($i = 0; $i < $n_; $i++) echo '.';
		echo $data_.'<br>';
	}
}

function print_form() {
	$inprogress = array();
	$files = glob(SPOOL.'inprogress/*');
	foreach($files as $k => $file) {
		$buf = file_get_contents($file);
		$buf2 = explode('|', $buf);
		if (count($buf2) == 2) {
			$buf_branch = trim($buf2[0]);
			$buf_package = trim($buf2[1]);
			if (!isset($inprogress[$buf_branch]))
				$inprogress[$buf_branch] = array();
			$inprogress[$buf_branch][$buf_package] = $k;
		}
	}

	$xml = shell_exec('python /home/packaging/ovd-deb/ovdeb.py --xml');
	$dom = new DomDocument('1.0', 'utf-8');
	$buf = @$dom->loadXML($xml);

	if (! $buf) {
		die('error03');
	}
	if (! $dom->hasChildNodes()) {
		die('error05');
	}
	$root_node = $dom->getElementsByTagname('root')->item(0);
	if (is_null($root_node)) {
		die('error06');
	}

	$packages = array();
	$branch_nodes = $root_node->getElementsByTagname('branch');
	foreach ($branch_nodes as $branch_node) {
		if ($branch_node->hasAttribute('version')) {
			$version = $branch_node->getAttribute('version');
			if (! isset($packages[$version]))
				$packages[$version] = array();
			$packages_node = $branch_node->getElementsByTagname('package');
			foreach ($packages_node as $package_node) {
				if ($package_node->hasAttribute('directory') && $package_node->hasAttribute('name')) {
					$name = $package_node->getAttribute('alias');
// 					$directory = $package_node->getAttribute('directory');
// 					$packages[$version][$name] = $directory;
					$packages[$version] []= $name;
				}
			}
		}
	}
// 	print_array($packages);echo "<hr>";
	krsort($packages);
// 	var_dump($packages);

	echo '<table border="1">';
	echo '<tr>';
	foreach( $packages as $branch => $v) {
		echo "<td><center>$branch</center></td>";
	}
	echo '</tr>';
	echo '<tr>';
	foreach( $packages as $branch => $v) {
	echo '<td style="vertical-align: top;">';

		sort($v);
		$v []= ''; // for generate all packages
// 		print_array($v);echo "<hr>";
		echo '<table border="0">';
		echo '<tr><th>Name</th><th>Repository</th><th>Action</th></tr>';
		foreach($v as $k2 => $package2) {
			if ($package2 == '') {
				$package_name = 'All';
				$package_command = '';
			}
			else {
				$package_name = $package2;
				$package_command = $package2;
			}
			echo '<tr>';
			echo '<td>';
			echo $package_name;
			echo '</td>';
			echo '<td>';
			echo "\n";
			if ($package_command != '') {
				if ( $branch == 'trunk' || $branch == '1.1')
					$branchstagging = $branch;
				else
					$branchstagging = $branch.'-staging';

				$cmd = "/home/gauvain/bin/ovdreprepro list $branchstagging $k2|grep source";
				$buf55 = shell_exec($cmd);
				preg_match('@.*svn([0-9]+).*@', $buf55, $matches);
				if (isset($matches[1]))
					echo 'svn'.(int)($matches[1]);
			}
			echo '</td>';
			echo '<td>';
			if ((! isset($inprogress[$branch][$package_command])) && ($branch != '1.1')) {
			echo '<form action="" method="POST">';
				echo '<input type="hidden" name="branch" value="'.$branch.'" />';
				echo '<input type="hidden" name="package" value="'.$package_command.'" />';
				echo '<input type="submit" name="add" value="'._('Generate').'" />';
			}
			elseif ($branch == '1.1') {
			}
			else {
				echo '<span style="color:red;">in progress ('.$inprogress[$branch][$package_command].')</span>';
			}
			echo '</form>';
			echo '</td>';
			echo '</tr>';
		}
		echo '</table>';
		echo '</td>';
	echo '</td>';
	}
	echo '<tr>';
	echo '</table>';

}

if (isset($_REQUEST['add'])) {
	if (isset($_REQUEST['branch']) && $_REQUEST['branch'] != '' && isset($_REQUEST['package'])) {
		$file_path = SPOOL.'/incoming/'.time().'_'.rand();
		file_put_contents($file_path, $_REQUEST['branch'].'|'.$_REQUEST['package']."\n");
// 		chmod($file_path, 0664);
		echo "job add<br><br>";
	}
}

print_form();
