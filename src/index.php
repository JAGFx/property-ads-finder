<?php

$basePath = 'data';
$annonces = json_decode(file_get_contents("$basePath/annonces.json"), true);

if (isset($_GET['hide'])) {
    $annonceIndex = array_keys(array_filter($annonces, function($a) { return $a['id'] == $_GET['hide']; }));
    foreach ($annonceIndex as $index) {
        $annonces[$index]['hide'] = !$annonces[$annonceIndex[0]]['hide'];
        $annonces[$index]['star'] = false;
        file_put_contents("$basePath/annonces.json", json_encode($annonces));
    }
}

if (isset($_GET['star'])) {
    $annonceIndex = array_keys(array_filter($annonces, function($a) { return $a['id'] == $_GET['star']; }));
    foreach ($annonceIndex as $index) {
        $annonces[$index]['hide'] = false;
        $annonces[$index]['star'] = !$annonces[$annonceIndex[0]]['star'];
        file_put_contents("$basePath/annonces.json", json_encode($annonces));
    }
}

if (isset($_GET['stars'])) {
    $annonces = array_values(array_filter($annonces, function($a) { return ($a['star'] ?? false); }));
} else if (!isset($_GET['all'])) {
    $annonces = array_values(array_filter($annonces, function($a) { return !($a['hide'] ?? false); }));
}

//echo '<pre>' . var_export($annonces, true) . '</pre>';

function dateToString(?string $dateString): ?string {
	if (!trim($dateString)) {
		return null;	
	}
	
	try {
	return (new Datetime($dateString))->format('d/m/Y');
	} catch (\Exception $e) {
		return null;
	}
}

?>

<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Annonces Maison</title>
	<style>
		table {
		  border: 1px solid #1C6EA4;
		  background-color: #EEEEEE;
		  width: 100%;
		  text-align: left;
		  border-collapse: collapse;
		}
		table td, tableth {
		  border: 1px solid #AAAAAA;
		  padding: 3px 6px;
		}
		table tr:nth-child(even) {
		  background: #D0E4F5;
		}
		table thead {
		  background: #1C6EA4;
		  background: -moz-linear-gradient(top, #5592bb 0%, #327cad 66%, #1C6EA4 100%);
		  background: -webkit-linear-gradient(top, #5592bb 0%, #327cad 66%, #1C6EA4 100%);
		  background: linear-gradient(to bottom, #5592bb 0%, #327cad 66%, #1C6EA4 100%);
		  border-bottom: 2px solid #444444;
		}
		table thead th {
		  font-size: 15px;
		  font-weight: bold;
		  color: #FFFFFF;
		  border-left: 2px solid #D0E4F5;
		}
		table thead th:first-child {
		  border-left: none;
		}
		table td img {
		  max-width: 500px;
	    }
	    table td {
	        text-align: center;
	        min-width: 100px;
    	  max-height: 375px;
       }
		.commentaire {
	        text-align: left;
			overflow: auto;
			display: block;
		}
.deleted {
color: red;
}
.stared {
font-weight: bold;
background-color: lightgreen;
}
	</style>
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
	<h1>Annonces maisons</h1>
	
	<p><strong><?= count($annonces) ?></strong> annonces selon nos critères depuis les sites : BienIci, Cimm Immobiler, Trenta Immobilier, Square Habitat, Meilleurs Agents, Century21, Safti, Aubreton, CapiFrance, IadFrance, Bièvre Immobiler, Imio, KdImmobilier, Klein Immobiler et ProxImmo</p>
	<p>Dernière mise à jour : <strong><?= date('d/m/Y H:i:s', filemtime("$basePath/annonces.json")) ?> UTC</strong></p>
	<p>
	    <a href="?">Voir les annonces</a><br />
		<a href="?all">Voir les annonces cachées</a><br />
		<a href="?stars">Voir les annonces favorites</a><br />
		<a target="_blank" href="https://www.leboncoin.fr/recherche?category=9&text=NOT%20construire%20NOT%20%22projet%20de%20construction%22%20NOT%20investisseurs%20NOT%20%22sera%20disponible%20fin%22&locations=Voiron_38500__45.36724_5.59114_5415_10000&immo_sell_type=old&real_estate_type=1&price=180000-330000&rooms=2-8&square=85-max">Aller sur la recherche LeBonCoin</a>
	</p>
	
	<table>
		<thead>
			<tr>
				<th>Date</th>
				<th>Photo</th>
				<th>Ville</th>
				<th>Surface</th>
				<th>Prix</th>
				<th>Site</th>
			</tr>
		</thead>
		
		<tbody>
			<?php foreach ($annonces as $annonce): ?>
			    <tr id="<?= $annonce['id'] ?>">
				    <td class="<?= ($annonce['star'] ?? false) ? 'stared' : '' ?> <?= ($annonce['deleted'] ?? false) || ($annonce['hide'] ?? false) ? 'deleted' : '' ?>"><?= dateToString($annonce['date']) ?></td>
				    <td><?= $annonce['image'] ? '<a target="_blank" href="' . $annonce['lien'] . '"><img src="' . $annonce['image'] . '" /></a>' : '-' ?></td>
				    <td><?= $annonce['ville'] ?></td>
				    <td class="commentaire"><?= str_replace(' - ', '<br>', $annonce['surface']) ?><br /><br /><?= $annonce['description'] ?><br /><a href="?hide=<?= $annonce['id'] ?>">Cacher</a><br /><a href="?star=<?= $annonce['id'] ?>">Favoris</a></td>
				    <td><?= number_format($annonce['prix'], 0, ',', ' ') . ' €' ?></td>
				    <td><?= $annonce['site'] ?></td>
			    </tr>
			<?php endforeach; ?>
		</tbody>
	</table>
</body>
</html>
