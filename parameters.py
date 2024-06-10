class Parameters:
    def __init__(self, most_pop=0,
                 dutch_places=2,
                 sim_entity=0,
                 pop_places=1.3,
                 cutoff_value=0,
                 superordinate_mention=2,
                 pplc_value=10,
                 pcli_value=15,
                 ppl_value=0,
                 pplaX_value=4,
                 pplg_value=0,
                 airp_value=10,
                 dutch_exonym_value=0,
                 NL_alt_names_value=6):

        self.most_pop_value = most_pop
        self.dutch_places_value = dutch_places
        self.sim_entity_value = sim_entity
        self.pop_places_value = pop_places
        self.cutoff_value = cutoff_value
        self.superordinate_mention_value = superordinate_mention
        self.pplc_value = pplc_value
        self.pcli_value = pcli_value
        self.ppl_value =ppl_value
        self.pplaX_value = pplaX_value
        self.pplg_value = pplg_value
        self.airp_value = airp_value
        self.dutch_exonym_value = dutch_exonym_value
        self.NL_alt_names_value = NL_alt_names_value
        # else:


    def get_most_pop_value(self):
        return self.most_pop_value

    def get_dutch_places_value(self):
        return self.dutch_places_value

    def get_sim_entity_value(self):
        return self.sim_entity_value

    def get_pop_places_value(self):
        return self.pop_places_value

    def get_superordinate_mention_value(self):
        return self.superordinate_mention_value

    def get_pplc_value(self):
        return self.pplc_value

    def get_pcli_value(self):
        return self.pcli_value

    def get_ppl_value(self):
        return self.ppl_value

    def get_pplaX_value(self):
        return self.pplaX_value

    def get_pplg_value(self):
        return self.pplg_value

    def get_airp_value(self):
        return self.airp_value

    def get_NL_alt_names_value(self):
        return self.NL_alt_names_value

    def get_dutch_exonym_value(self):
        return self.dutch_exonym_value

    def get_cutoff_value(self):
        return self.cutoff_value
# obj = Paramaters()
# print(obj.get_most_pop_value())