import fs from 'fs';
import feed from 'feed';
import fetch from 'node-fetch';
const basePath = '/srv/src/data/';

const rss = new feed.Feed({
  title: 'Annonces maisons',
  description: 'Liste les annonces de maisons',
  id: 'https://pixel-server.ovh/maisons',
  link: 'https://pixel-server.ovh/maisons',
  language: 'fr',
  feedLinks: {
    rss: 'https://pixel-server.ovh/maisons/rss.xml',
  },
  author: {
    name: 'Valentin Saugnier - Juline Scoarnec',
    email: 'valentin.s.10@gmail.com',
    link: 'https://valentin-saugnier.fr'
  },
  ttl: 15
});

fetch( 'https://www.villes-voisines.fr/getcp.php?cp=38500&rayon=15' )
    .then( async response => {
        const data = await response.json();
        let villes = Object.values( data ).map( v => {
            return v.nom_commune
                    .toUpperCase()
                    .replace( 'ST', 'SAINT' )
                    .replace( / /g, '-' )
                    .normalize( "NFD" )
                    .replace( /[\u0300-\u036f]/g, "" );
        } );
    
        let oldAnnonces = [];
    
        try {
            oldAnnonces = JSON.parse( fs.readFileSync( `${ basePath }annonces.json` ) )
                              .filter( a => villes.includes( a.ville.toUpperCase().replace( 'ST', 'SAINT' ).replace(
                                  / /g,
                                  '-' ).normalize( "NFD" ).replace( /[\u0300-\u036f]/g, "" ).trim() ) );
            console.log( oldAnnonces.length, 'annonces existantes' );
        } catch ( e ) {
        }
    
        /*for (const annonce of oldAnnonces) {
         annonce.id = annonce.site + '_' + annonce.id;
         }
     
         fs.writeFileSync('annonces.json', JSON.stringify(newAnnonces));
     
         exit(0);*/
    
        let newAnnonces = JSON.parse( fs.readFileSync( `${ basePath }newAnnonces.json` ) )
                              .filter( a => villes.includes( a.ville.toUpperCase().replace( 'ST', 'SAINT' ).replace(
                                  / /g,
                                  '-' ).normalize( "NFD" ).replace( /[\u0300-\u036f]/g, "" ).trim() ) );
    
        for ( const annonce of newAnnonces ) {
            if ( !annonce.date ) {
                annonce.date = new Date();
            }
        }
    
        for ( const oldAnnonce of oldAnnonces ) {
            const newAnnonce = newAnnonces.find( a => a.id === oldAnnonce.id );
        
            if ( newAnnonce ) {
                if ( newAnnonce.prix === oldAnnonce.prix && oldAnnonce.date ) {
                    newAnnonce.date = oldAnnonce.date;
                }
            
                newAnnonce.hide = oldAnnonce.hide;
                newAnnonce.star = oldAnnonce.star;
            } else {
                oldAnnonce.deleted = true;
                newAnnonces.push( oldAnnonce );
            }
        }
    
        newAnnonces = newAnnonces.sort( ( a, b ) => a.date < b.date ? 1 : -1 );
    
        fs.writeFile( `${ basePath }annonces.json`, JSON.stringify( newAnnonces ), function ( err ) {
            if ( err ) return console.error( err );
            console.log( newAnnonces.length );
        } );
    
        newAnnonces.forEach( item => {
            if ( !item.hide && !item.deleted ) {
                rss.addItem( {
                    id:          item.site + '_' + item.id,
                    title:       item.ville + ' - ' + item.prix + ' €',
                    link:        item.lien,
                    date:        new Date( item.date ),
                    description: item.surface,
                    content:     item.description,
                    image:       item.image
                } );
            }
        } );
    
        fs.writeFile( `${ basePath }rss.json`, rss.rss2(), function ( err ) {
            if ( err ) return console.error( err );
        } );
    } )
