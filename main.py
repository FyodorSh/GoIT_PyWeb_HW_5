import sys
from datetime import datetime, timedelta
from pprint import pprint

import platform
import aiohttp
import asyncio


class PB_Exchange_Rates():

    BASE_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='

    async def get_rates_to_date(self, url: str, session):
        try:
            async with session.get(url) as response:
                print(f'getting -> {url}')
                if response.status == 200:
                    return await response.json()
                else:
                    return {}
        except RuntimeError as e:
            return {}

    async def bound_fetch(self, sem, url, session):
        async with sem:
            await self.get_rates_to_date(url, session)

    async def get_rates_by_tasks(self, urls: list):
        tasks = []
        responses = []
        async with aiohttp.ClientSession() as session:
            for url in urls:
                task = asyncio.ensure_future(self.get_rates_to_date(url, session))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

        return responses

    def get_rates(self, qty_dates: int):
        urls = [f'{self.BASE_URL + date}' for date in self.get_list_dates(qty_dates)]
        result = asyncio.run(self.get_rates_by_tasks(urls))
        return [self.convert_result(curr_rate) for curr_rate in result]

    @staticmethod
    def convert_result(data: dict) -> dict:
        if data:
            curr_rates = {}
            currencies_for_result = ['EUR', 'USD']
            for curr in currencies_for_result:
                curr_rates.update({curr: {'purchase': curr_rate['purchaseRateNB'], 'sale': curr_rate['saleRateNB']}
                                   for curr_rate in result['exchangeRate'] if curr_rate['currency'] == curr})

            converted_result = {result['date']: curr_rates}
            return converted_result
        
    @staticmethod
    def get_list_dates(qty_dates: int) -> list:
        today = datetime.today()
        list_dates = []
        for x in range(0, qty_dates):
            list_dates.append((today - timedelta(days=x)).strftime('%d.%m.%Y'))
        return list_dates


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        qty_dates = 5
    else:
        qty_dates = int(args[0])

    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    exchange = PB_Exchange_Rates()
    result = exchange.get_rates(qty_dates)
    pprint(result)
