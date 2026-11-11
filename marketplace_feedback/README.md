# Marktplaatsfeedback

Leest de feedback van een marktplaatskanaal in Channable (eerst Amazon) in Odoo in,
zodat je de artikels in Odoo vervolledigt in plaats van te pendelen tussen
Channable en Odoo.

## Vooraf (eenmalig)

* In Studio: `x_value` op het model *Product property value* niet verplicht maken.
  De module maakt lege property-rijen aan voor wat Amazon vraagt.
* De module maakt bij installatie zelf het vinkje **Voor Amazon** (`x_for_amazon`)
  aan op de property-rijen, zoals Studio dat zou doen. Wil je het zien in de
  propertylijst op de productfiche: sleep het veld daar met Studio in de lijst.

## De cyclus

1. **Channable**: Amazon-kanaal › Resultaat › Feedback › *Download as CSV*.
2. **Odoo**: Verkoop › Configuratie › Marktplaatsen › **Feedback importeren** ›
   Nieuw › bestand kiezen › *Verwerken*. De vorige feedback wordt vervangen.
   Artikels worden gezocht op interne referentie (= id in Channable), anders op EAN.
3. **Algemeen niveau** (enkel als de import nieuwe velden meldt):
   Configuratie › Marktplaatsen › **Marktplaatsvelden**. Per veld één keer beslissen:
   * *Property op het artikel*: kies een bestaande property of vul *Nieuwe property*
     in en klik **Properties aanmaken**.
   * *Ander gegeven in Odoo*: naam/beschrijving in het Frans, prijs, gewicht, EAN …
   * *Opgelost in Channable*: vaste waarde of regel in Channable.
   * *Handmatig (Seller Central)* of *Negeren*.
   Velden uit de Amazon-run van november 2026 staan er al met een voorstel.
4. **Artikelniveau**: voor elk veld met een property krijgt elk gemeld artikel een
   property-rij (leeg als ze nog niet bestond) met het vinkje *Voor Amazon*.
   Invullen kan op de productfiche of, sneller, in Verkoop › Producten ›
   **Ontbrekende properties invullen** (gegroepeerd per veld, Enter = volgende regel).
5. **Channable**: koppel de properties (pp_…) aan de Amazon-velden en vink in
   Marktplaatsvelden *Ingesteld in Channable* aan. Daarna Channable laten syncen
   met Amazon, en terug naar stap 1.

## Waar zie je wat

* Productfiche › tab **Marktplaatsen**: alle meldingen van de laatste import voor
  dit artikel, met wat te doen; waarden van properties kun je er meteen invullen.
* Verkoop › Producten › **Marktplaatsfeedback**: alle meldingen (filter *Te doen in
  Odoo*, *Niet gevonden in Odoo*, groeperen per product, veld of producttype).
* Productlijst: kolom *Marktpl.* en filter *Met marktplaatsfeedback*.

## Goed om te weten

* Een melding hoort bij de laatste import; het vinkje *Voor Amazon* op de
  property-rij blijft staan, ook als Amazon niet meer klaagt.
* Waarden `undefined` of leeg tellen als niet ingevuld.
* Channable heeft geen API voor feedback; vandaar de CSV. Automatisch ophalen
  kan later via de Amazon SP-API.
