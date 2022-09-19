TRAIN_TICKET_SERVICES = {
    'ts-assurance-service': [
        {'method': 'GET', 'url': '/api/v1/assuranceservice/assurances/types'},
        {'method': 'GET', 'url': '/api/v1/assuranceservice/assurances/'}
    ],
    'ts-auth-service': [
        {'method': 'POST', 'url': '/api/v1/users/login'}
    ],
    'ts-basic-service': [
        {'method': 'GET', 'url': '/api/v1/basicservice/basic/'},
        {'method': 'POST', 'url': '/api/v1/basicservice/basic/travel'}],
    'ts-config-service': [{'method': 'GET',
                           'url': '/api/v1/configservice/configs/DirectTicketAllocationProportion'}],
    'ts-consign-service': [
        {'method': 'GET',
         'url': '/api/v1/consignservice/consigns/account/'}],
    'ts-contacts-service': [
        {'method': 'GET',
         'url': '/api/v1/contactservice/contacts/'}],
    'ts-food-map-service': [
        {'method': 'POST', 'url': '/api/v1/foodmapservice/foodstores'},
        {'method': 'GET', 'url': '/api/v1/foodmapservice/trainfoods/'}],
    'ts-food-service': [
        {'method': 'POST', 'url': '/api/v1/foodservice/orders'},
        {'method': 'GET',
         'url': '/api/v1/foodservice/foods/'}],
    'ts-order-other-service': [
        {'method': 'GET',
         'url': '/api/v1/orderOtherService/orderOther/'},
        {'method': 'POST',
         'url': '/api/v1/orderOtherService/orderOther/refresh'},
        {'method': 'POST',
         'url': '/api/v1/orderOtherService/orderOther/tickets'},
        {'method': 'POST', 'url': '/api/v1/orderOtherService/orderOther'},
    ],
    'ts-order-service': [
        {'method': 'GET', 'url': '/api/v1/orderservice/order/'},
    ],
    'ts-preserve-other-service': [
        {'method': 'POST', 'url': '/api/v1/preserveotherservice/preserveOther'}
    ],
    'ts-preserve-service': [
        {'method': 'POST', 'url': '/api/v1/preserveservice/preserve'}
    ],
    'ts-price-service': [
        {'method': 'GET', 'url': '/api/v1/priceservice/prices/'},
    ],
    'ts-route-service': [
        {'method': 'GET', 'url': '/api/v1/routeservice/routes/'}],
    'ts-seat-service': [
        {'method': 'POST', 'url': '/api/v1/seatservice/seats/left_tickets'},
        {'method': 'POST', 'url': '/api/v1/seatservice/seats'}],
    'ts-security-service': [
        {'method': 'GET', 'url': '/api/v1/securityservice/securityConfigs/'}
    ],
    'ts-station-service': [
        {'method': 'GET', 'url': '/api/v1/stationservice/stations/id/'},
        {'method': 'POST', 'url': '/api/v1/stationservice/stations/namelist'}
    ],
    'ts-ticketinfo-service': [
        {'method': 'GET', 'url': '/api/v1/ticketinfoservice/ticketinfo/'},
        {'method': 'POST', 'url': '/api/v1/ticketinfoservice/ticketinfo'}
    ],
    'ts-train-service': [
        {'method': 'GET', 'url': '/api/v1/trainservice/trains/ZhiDa'},
        {'method': 'GET', 'url': '/api/v1/trainservice/trains/GaoTieOne'},
        {'method': 'GET', 'url': '/api/v1/trainservice/trains/TeKuai'},
        {'method': 'GET', 'url': '/api/v1/trainservice/trains/DongCheOne'},
        {'method': 'GET', 'url': '/api/v1/trainservice/trains/GaoTieTwo'}
    ],
    'ts-travel-service': [
        {'method': 'GET', 'url': '/api/v1/travelservice/routes/'},
        {'method': 'GET', 'url': '/api/v1/travelservice/train_types/'},
        {'method': 'POST', 'url': '/api/v1/travelservice/trip_detail'},
        {'method': 'POST', 'url': '/api/v1/travelservice/trips/left'}
    ],
    'ts-travel2-service': [
        {'method': 'GET', 'url': '/api/v1/travel2service/train_types/'},
        {'method': 'POST', 'url': '/api/v1/travel2service/trip_detail'},
        {'method': 'POST', 'url': '/api/v1/travel2service/trips/left'}
    ],
    'ts-user-service': [
        {'method': 'GET', 'url': '/api/v1/userservice/users/id/'}
    ],
    'ts-verification-code-service': [
        {'method': 'GET', 'url': '/api/v1/verifycode/generate'},
        {'method': 'GET', 'url': '/api/v1/verifycode/verify/'},
    ]
}
