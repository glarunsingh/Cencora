import azure.functions as func

from Definitive.main import bp_definitive
from DrugChannel.main import bp_drugchannel
from BeckerHospital.main import bp_beckerhospital
from Advisory.main import bp_advisory
from HIMSS.himss import bp_himss
from BingNews.main import bp_bingnews

app = func.FunctionApp()

app.register_blueprint(bp_drugchannel)
app.register_blueprint(bp_beckerhospital)
app.register_blueprint(bp_advisory)
app.register_blueprint(bp_definitive)
app.register_blueprint(bp_himss)
app.register_blueprint(bp_bingnews)