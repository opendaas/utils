<?php

define('SPOOL', '/var/spool/ovdeb');
define('CACHE', '/var/cache/ovdeb');

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

if (isset($_REQUEST['addjob'])) {
	if (isset($_REQUEST['branch']) && $_REQUEST['branch'] != '' &&
        isset($_REQUEST['package'])) {
		$file_path = SPOOL.'/incoming/'.time().'_'.rand();
		file_put_contents($file_path, $_REQUEST['branch'].
                          '|'.$_REQUEST['package']."\n");
        sleep(1);
        header('Location: '.$_SERVER['REQUEST_URI']);
        die();
	}
}

$inprogress = array();
foreach(glob(SPOOL.'/inprogress/*') as $k => $file) {
	$args = explode('|', file_get_contents($file));
	if (count($args) <= 2) {
		$branch = trim($args[0]);
		$package = trim($args[1]);
		if (!isset($inprogress[$branch]))
			$inprogress[$branch] = array();
		$inprogress[$branch][$package] = '';
	}
}

$xml = file_get_contents(CACHE.'/repo.xml');
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

$branches = array();
$branch_nodes = $root_node->getElementsByTagname('branch');
foreach ($branch_nodes as $branch_node) {
	if ($branch_node->hasAttribute('repo')) {
		$bname = $branch_node->getAttribute('repo');
		if (! isset($branches[$bname]))
			$branches[$bname] = array();
		$branches_node = $branch_node->getElementsByTagname('package');
		foreach ($branches_node as $package_node) {
			if ($package_node->hasAttribute('alias')) {
				$alias = $package_node->getAttribute('alias');
				$branches[$bname][$alias]['name'] =
                    $package_node->getAttribute('name');
				$branches[$bname][$alias]['version'] =
                    $package_node->getAttribute('version');
			}
		}
	}
}
krsort($branches);

echo '<table border="1"><tr>';
foreach( $branches as $branch => $package) {
	echo "<td><center>$branch</center></td>";
}
echo '</tr>';

foreach( $branches as $branch => $package) {
	echo '<td style="vertical-align: top;">';
	$package['']= Array('name' => 'All'); // for generate all packages
	echo '<table border="0">';
	echo '<tr><th>Name</th><th>Repository</th><th>Action</th></tr>';
	foreach($package as $alias => $infos) {
		echo '<tr><td>'.$infos['name'].'</td><td>'.$infos['version'].'</td><td>';
		if (! isset($inprogress[$branch][$alias])) {
			echo '<form action="" method="POST">';
            echo '<input type="hidden" name="branch" value="'.$branch.'" />';
            echo '<input type="hidden" name="package" value="'.$alias.'" />';
			echo '<input type="submit" name="addjob" value="Generate" /></form>';
		}
		else {
			echo '<span style="color:red;"><center>X<center></span>';
		}
		echo '</td></tr>';
	}
	echo '</table></td></td>';
}
echo '<tr></table>';
