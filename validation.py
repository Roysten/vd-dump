import sys
import unittest

assertEqual = unittest.TestCase().assertEqual

EXPECTATIONS = [
    [66443,"11 novemberviering","11 no·vem·ber·vie·ring",[{"d":"viering op de dag van de $wapenstilstand$ (2), waarop de doden van de beide wereldoorlogen herdacht worden"}],[]],
    [4754,"adé","adé (niet: a·dé)",[{"d":"(informeel) zie $adieu$"},{"d":"jongere broer of zuster"}],[]],
    [4937,"adequaat","ade·quaat (niet: a·dequ·aat)",[{"d":"overeenstemmend met het voorbeeld of met het object","s":"gelijkwaardig"},{"d":"geschikt voor het beoogde doel"}],[]],
    [4938,"adequatie","ade·qua·tie (niet: a·dequ·atie)",[{"d":"het adequaat-zijn","a":"inadequatie"}],[]],
    [4939,"adequeren","ade·que·ren (niet: a·dequ·eren)",[{"d":"gelijk of effen maken","s":"vereffenen"},{"d":"gelijkstellen"}],[["","","onvoltooid tegenwoordige tijd","onvoltooid verleden tijd"],["1e persoon enkelvoud","ik","adequeer","adequeerde"],["2e persoon enkelvoud","jij","adequeert","adequeerde"],["3e persoon enkelvoud","hij/zij/het","adequeert","adequeerde"],["1e persoon meervoud","wij","adequeren","adequeerden"],["2e persoon meervoud","jullie","adequeren","adequeerden"],["3e persoon meervoud","zij","adequeren","adequeerden"],["beleefdheidsvorm","u","adequeert","adequeerde"],["voltooid deelwoord","geadequeerd"]]],
    [4687,"ad deliberandum","ad de·li·be·ran·dum",[{"d":"om zich over te beraden"}],[]],
    [4688,"addendum","ad·den·dum",[{"d":"bijvoegsel, toevoegsel (van een boek)"}],[]],
    [4917,"adenectomie","ade·nec·to·mie (niet: a·denectomie)",[{"d":"adenotomie"}],[]],
    [4918,"adenine","ade·ni·ne (niet: a·denine)",[{"d":"purinebase behorend tot de bestanddelen van nucleïnezuren"}],[]],
    [4919,"adenitis","ade·ni·tis (niet: a·denitis)",[{"d":"ontsteking van een lymfklier"}],[]],
    [4689,"addenoj","ad·de·noj",[{"d":"zie $attenoje$"}],[]],
    [4920,"adenocarcinoom","ade·no·car·ci·noom (niet: a·denocarcinoom)",[{"d":"kankergezwel dat ontstaat in cellen met klierachtige eigenschappen"}],[]],
    [4690,"addenom","ad·de·nom",[{"d":"zie $attenoje$"}],[]],
    [4924,"adenoma","ade·no·ma (niet: a·denoma)",[{"d":"zie $adenoom$"}],[]],
    [4925,"adenomalacie","ade·no·ma·la·cie (niet: a·denomalacie)",[{"d":"(medisch) klierverweking"}],[]],
    [4926,"adenoom","ade·noom (niet: a·denoom)",[{"d":"goedaardig gezwel dat uit klierweefsel voortkomt","vv":"adenoma"}],[]],
]

def validate(word, index):
    try:
        if index < len(EXPECTATIONS):
            assertEqual(EXPECTATIONS[index], word)
    except AssertionError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
