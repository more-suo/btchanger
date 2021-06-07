from flask import Flask
from flask_restful import Api, Resource, reqparse, abort
from datetime import datetime, timedelta
import requests

# The file lies in .gitignore, so it must be created if you want to use the API
import secret_keys


app = Flask(__name__)
api = Api(app)

coinlayer_base_url = "http://api.coinlayer.com/"


def valid_date(date):
    try:
        date = datetime.strptime(date, "%d-%m-%Y")
    except ValueError:
        raise ValueError("Given date format is invalid")

    if date > datetime.utcnow() or date < datetime.strptime("2012", "%Y"):
        raise ValueError("Given date is out of range")

    return date


exchange_rate_args = reqparse.RequestParser()
exchange_rate_args.add_argument("start_date", type=valid_date)
exchange_rate_args.add_argument("end_date", type=valid_date)
exchange_rate_args.add_argument("date", type=valid_date)


meta_information = {
    "source": coinlayer_base_url,
}


def abort_if_argument_is_missing(a, b):
    if a is None or b is None:
        abort(400, errors=["One of the dates are missing."])


def abort_if_end_date_is_earlier(start_date, end_date):
    r""" Aborts if end date is earlier than the start date

    :param start_date: Start date
    :type start_date: datetime
    :param end_date: End date
    :type end_date: datetime
    """
    if start_date > end_date:
        abort(400, errors=["End date is earlier than the start date."])


def get_rate(start_date=None, end_date=None):
    r"""Returns the BTC to USD exchange rate for given dates.
        If the dates aren't given returns the current rate.

    :param start_date: The start date of the needed period,
                if start_date isn't given it will be set to today's date, defaults to None
    :type start_date: datetime, optional
    :param end_date: The end date of the needed period,
                if end_date isn't given it will be set to start_date, defaults to None
    :type end_date: datetime, optional
    :return: A dictionary of exchange rates for needed dates
    :rtype: dict
    """
    exchange_rate_data = {}
    coinlayer_api_key = secret_keys.COINLAYER_API
    time_delta = timedelta(days=1)

    if start_date is None:
        start_date = end_date = datetime.utcnow()
    elif end_date is None:
        end_date = start_date

    while start_date <= end_date:
        response = requests.get(coinlayer_base_url + start_date.strftime("%Y-%m-%d"),
                                params={"access_key": coinlayer_api_key})
        exchange_rate_data[start_date.strftime("%d-%m-%Y")] = response.json()["rates"]["BTC"]
        start_date += time_delta

    return exchange_rate_data


class ExchangeRate(Resource):
    def get(self):
        args = exchange_rate_args.parse_args()
        date, start_date, end_date = args["date"], args["start_date"], args["end_date"]

        if date is not None:
            data = get_rate(date)
        elif start_date is None and end_date is None:
            data = get_rate()
        else:
            abort_if_argument_is_missing(start_date, end_date)
            abort_if_end_date_is_earlier(start_date, end_date)
            data = get_rate(start_date, end_date)

        return {
            "links": meta_information,
            "data": data,
        }, 200


api.add_resource(ExchangeRate, "/api/rate")


if __name__ == "__main__":
    app.run()
