# Note: this is highly unsafe, please move this to somewhere else before publicizing
# Also change the values if you don't wipe the commit history
# Yours truly, -Cobble

from prod import PROD

MOD_LOGS = "https://discord.com/api/webhooks/1102975443746959460/KTC6Ep2qfvnKXfmcr3lazHD2rT8NdFiJkx20H7ataxOVjQlbWJgSwiaRRVwsPY9fpCVT"
PROJ_LOGS = "https://discord.com/api/webhooks/1122512713831174176/Ihze07U1HQ8h4YDcm0TPuRPR8syySm9mkG6OFVFDTWsPBOT6jg3MEnWPfB5jmv-cmLP_"
FILES_TOKEN = "torsoHowardzetta6"
BACKUPS_TOKEN = "supersecrettoken69"

if PROD == 1:
    DATA = "/var/DatapackHub/"

    class github:
        client_id = "8a0527a3da5b002db8c9"
        client_secret = "c3dd98c1ed8acc65989824e70d61fd49cf60640d"

else:
    DATA = ""

    class github:
        client_id = "cd983835f4e37148ba77"
        client_secret = "56414b10caf5394328730deba6b41a6f38bfee8f"


valid_tags = [
    "Adventure",
    "Magic",
    "Minecraft but",
    "Cursed",
    "World Generation",
    "Tools / Equipment",
    "German",
    "Recipe",
    "Quality of Life",
    "Items / Blocks",
    "Cosmetic",
    "Miscellaneous",
    "Utility",
    "Vanilla+",
]

valid_types = ["datapack"]
