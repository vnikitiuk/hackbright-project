'use strict';

let chart;

function showStockPrice(event) {
    event.preventDefault();

    const symbol = document.querySelector('#username').value;

    fetch(`/quote.json?symbol=${symbol}`)
        .then((response) => response.json())
        .then((jsonData) => {
            document.querySelector('#stock-info').innerHTML = [jsonData.symbol, jsonData.price];

            const chart_info = jsonData.chart_info.map((dailyPrice) => ({
                x: dailyPrice.time,
                y: dailyPrice.close_price,
            }));

            if (chart) {
                chart.destroy();
            }

            chart = new Chart(document.querySelector('#line-time'), {
                type: 'line',
                data: {
                    datasets: [
                      {
                        label: jsonData.name,
                        data: chart_info, // equivalent to data: data
                      },
                    ],
                  },
                options: {
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                tooltipFormat: 'LLLL dd', // Luxon format string
                                unit: 'day',
                            },
                        },
                    },
                },
            });
        });
}

document.querySelector('#get-stock-price').addEventListener('click', showStockPrice);