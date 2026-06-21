import { useEffect, useState } from "react";
import axiosInstance from "../../api/axiosConfig";
import { Pencil, Trash2 } from 'lucide-react';




const CategoriesList = () => {

    const [categories, setCategories] = useState([]);

    useEffect(() => {
        // Simulate fetching categories from an API
       
        axiosInstance
        .get('/finances/categories/')
        .then(res => {
            setCategories(res.data);
        })
        .catch(console.error)
        .finally(() => {
            // You can set a loading state here if needed
        });  
           
    }, []);

  return (
    <div className="categories-card--large">

        <div className="categories-card--large__body">
            <h2 className="categories-card--large__header">Categories Manager</h2>
            <div className="ctg-container">
                {categories.length === 0 ? (
                <div>Loading categories...</div>
                ) : (
                categories.map((category, index) => (
                    <div className="ctg-line">
                        <div className="ctg-item" 
                        style=
                        {{
                            color: category?.color ?? '#888',
                            background: (category?.color ?? '#888') + '1a',
                            border: `1px solid ${(category?.color ?? '#888')}80` 
                        }} 
                        key={index}>{category.name}
                        </div>
                        <div className="ctg-actions">
                            <button className="ctg-button" onClick={() => alert(`Edit category: ${category.name}`)}><Pencil size={14} /></button>
                            <button className="ctg-button" onClick={() => alert(`Delete category: ${category.name}`)}><Trash2 size={14} /></button>
                        </div>
                    </div>
                    
                    
                ))
                )}
            </div>
            <div>Add category</div>

        </div>
        
     
    </div>
  );
}

export default CategoriesList;