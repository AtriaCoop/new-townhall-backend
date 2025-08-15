from django.test import SimpleTestCase
from posts.profanity import censor_text


class CensorTextTests(SimpleTestCase):
    def test_examples(self):
        self.assertEqual(censor_text("this is shit"), "this is ****")
        self.assertEqual(censor_text("ShIt happens"), "**** happens")
        self.assertEqual(censor_text("what the hell?"), "what the ****?")
        self.assertEqual(censor_text("class"), "class")  # no false positive
        self.assertEqual(censor_text("you BITCH!"), "you *****!")
        self.assertEqual(censor_text("motherfucker"), "************")
        self.assertEqual(censor_text("fuck you"), "**** you")
        self.assertEqual(censor_text("motherfucker's"), "************'s")
        self.assertEqual(censor_text("shit-faced"), "****-faced")
