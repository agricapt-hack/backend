from flask import Blueprint, request, jsonify
from app.service.hello_service import get_hello_message
from app.models.productservice_model import AddProductSchema, AddServiceSchema
from pydantic import ValidationError
from app.mongo.agri_handlers import AGRI_PRODUCT_HANDLER, AGRI_SERVICE_HANDLER,  AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER, FIELD_HANDLER

productservice_blueprint = Blueprint('productservice', __name__)


@productservice_blueprint.route('/add-product', methods=['POST'])
def add_product():
    """
        Sample product JSON:
        {
        "product_id": "12345",
        "name": "Organic Fertilizer : Urea 222",
        "category": "Fertilizers",
        "price": 25.99,
        "description": "High-quality organic fertilizer for better crop yield.",
        "usage": "Apply 50 kg per hectare before planting.",
        "image_url": "http://example.com/image.jpg",
        "provider": {
            "name": "AgriTech Solutions",
            "contact": "123-456-7890",
            "email": "info@agritechsolutions.com",
            "address": "123 Agri Lane, Farm City, Country"
        }
    }
    """
    data = request.get_json()
    try:
        validated = AddProductSchema(**data)
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.errors()}), 400

    try:
        AGRI_PRODUCT_HANDLER.add_product(validated.dict())
        return jsonify({'success': True, 'message': 'Product added successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@productservice_blueprint.route('/add-service', methods=['POST'])
def add_service():
    """
        Sample service JSON:
        {
        "service_id": "serv_001",
        "name": "Soil Testing",
        "description": "Comprehensive soil testing for nutrient analysis.",
        "image_url": "http://example.com/service.jpg",
        "price": 50.00,

        "provider": {
            "name": "AgriTech Solutions",
            "contact": "123-456-7890",
            "email": "info@agritechsolutions.com",
            "address": "123 Agri Lane, Farm City, Country"
        }
    }
    """
    data = request.get_json()
    try:
        validated = AddServiceSchema(**data)
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.errors()}), 400

    try:
        AGRI_SERVICE_HANDLER.add_service(validated.dict())
        return jsonify({'success': True, 'message': 'Service added successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@productservice_blueprint.route('/get-product', methods=['POST'])
def get_product():
    data = request.get_json()
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required'}), 400
    product = AGRI_PRODUCT_HANDLER.get_product_by_id(product_id)

    if product:
        # Convert _id to string if necessary
        if isinstance(product, dict) and '_id' in product:
            product['_id'] = str(product['_id'])
            del product['vector']  # Assuming vector is not needed in the response
        return jsonify({'success': True, 'data': product}), 200
    else:
        return jsonify({'success': False, 'message': 'Product not found'}), 404

@productservice_blueprint.route('/delete-product', methods=['POST'])
def delete_product():
    data = request.get_json()
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'message': 'Product ID is required'}), 400
    try:
        AGRI_SERVICE_HANDLER.delete_by_id(unique_field='product_id', value=product_id)
        return jsonify({'success': True, 'message': 'Product deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@productservice_blueprint.route('/get-service', methods=['POST'])
def get_service():
    data = request.get_json()
    service_id = data.get('service_id')
    if not service_id:
        return jsonify({'success': False, 'message': 'Service ID is required'}), 400
    service = AGRI_SERVICE_HANDLER.get_service_by_id(service_id)

    if service:
        # Convert _id to string if necessary
        if isinstance(service, dict) and '_id' in service:
            service['_id'] = str(service['_id'])
            del service['vector']
        return jsonify({'success': True, 'data': service}), 200
    else:
        return jsonify({'success': False, 'message': 'Service not found'}), 404

@productservice_blueprint.route('/delete-service', methods=['POST'])
def delete_service():
    data = request.get_json()
    service_id = data.get('service_id')
    if not service_id:
        return jsonify({'success': False, 'message': 'Service ID is required'}), 400
    try:
        AGRI_SERVICE_HANDLER.delete_by_id(unique_field='service_id', value=service_id)
        return jsonify({'success': True, 'message': 'Service deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@productservice_blueprint.route('/get-all-products', methods=['POST'])
def get_all_products():
    try:
        products = AGRI_PRODUCT_HANDLER.get_all()
        if not products:
            return jsonify({'success': False, 'message': 'No products found'}), 404
        # Convert _id to string if necessary
        for product in products:
            if isinstance(product, dict) and '_id' in product:
                product['_id'] = str(product['_id'])
                del product['vector']
        return jsonify({'success': True, 'products': products}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@productservice_blueprint.route('/get-all-services', methods=['POST'])
def get_all_services():
    try:
        services = AGRI_SERVICE_HANDLER.get_all()
        if not services:
            return jsonify({'success': False, 'message': 'No services found'}), 404
        # Convert _id to string if necessary
        for service in services:
            if isinstance(service, dict) and '_id' in service:
                service['_id'] = str(service['_id'])
                del service['vector']
        return jsonify({'success': True, 'services': services}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@productservice_blueprint.route('/get-all-notifications-by-hub', methods=['POST'])
def get_all_notifications():
    """
    Sample request JSON:
    {
        "hub_id": "hub_1"
    }
    """
    data = request.get_json()
    hub_id = data.get('hub_id')

    if not hub_id:
        return jsonify({'success': False, 'message': 'Hub ID is required'}), 400

    try:
        notifications = AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.get_by_query(
            query={'sensor_hub_id': hub_id}
        )
        if not notifications:
            return jsonify({'success': False, 'message': 'No notifications found for the given Hub ID'}), 404
        # Convert _id to string if necessary
        for notification in notifications:
            if isinstance(notification, dict) and '_id' in notification:
                notification['_id'] = str(notification['_id'])
                
        return jsonify({'success': True, 'notifications': notifications}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@productservice_blueprint.route('/get-all-notifications-by-user', methods=['POST'])
def get_all_notifications_by_user():
    """
    Sample request JSON:
    {
        "user_id": "user_1"
    }
    """
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400

    try:
        all_fields = FIELD_HANDLER.get_fields_by_user_id(user_id)
        hub_ids = [field['sensor_hub_id'] for field in all_fields]
        if not hub_ids:
            return jsonify({'success': False, 'message': 'No fields found for the given User ID'}), 404
        notifications = AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.get_by_query(
            query={'sensor_hub_id': {'$in': hub_ids}}
        )
        if not notifications:
            return jsonify({'success': False, 'message': 'No notifications found for the given User ID'}), 404
        
        # Convert _id to string if necessary
        for notification in notifications:
            if isinstance(notification, dict) and '_id' in notification:
                notification['_id'] = str(notification['_id'])
        
        return jsonify({'success': True, 'notifications': notifications}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500