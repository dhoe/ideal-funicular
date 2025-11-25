/**
 * Graphical Code Editor - Main Application
 *
 * A zoomable code visualization tool with three detail levels:
 * 1. Architecture: Boxes and arrows overview
 * 2. Signatures: Function signatures visible
 * 3. Code: Full source code
 */

class GraphicalCodeEditor {
    constructor() {
        this.modules = [];
        this.currentZoom = 1;
        this.zoomLevels = {
            ARCHITECTURE: { min: 0, max: 0.7, name: 'Architecture' },
            SIGNATURES: { min: 0.7, max: 1.5, name: 'Signatures' },
            CODE: { min: 1.5, max: 4, name: 'Code' }
        };

        this.nodeWidth = 200;
        this.nodeMinHeight = 60;
        this.nodeSpacing = 40;

        this.init();
    }

    init() {
        this.setupSVG();
        this.setupEventListeners();
        this.loadSampleData();
    }

    setupSVG() {
        const container = document.getElementById('canvas-container');
        this.svg = d3.select('#canvas');
        this.zoomGroup = this.svg.select('#zoom-group');
        this.linksLayer = this.svg.select('#links-layer');
        this.nodesLayer = this.svg.select('#nodes-layer');

        // Setup zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => this.handleZoom(event));

        this.svg.call(this.zoom);

        // Initial view
        const width = container.clientWidth - 220;
        const height = container.clientHeight;
        this.svg.call(this.zoom.transform, d3.zoomIdentity.translate(width / 4, height / 4));
    }

    setupEventListeners() {
        // Zoom controls
        document.getElementById('zoom-in').addEventListener('click', () => this.zoomBy(1.3));
        document.getElementById('zoom-out').addEventListener('click', () => this.zoomBy(0.7));
        document.getElementById('zoom-reset').addEventListener('click', () => this.resetView());

        // Zoom slider
        const slider = document.getElementById('zoom-slider');
        slider.addEventListener('input', (e) => {
            const scale = parseFloat(e.target.value);
            this.setZoom(scale);
        });

        // File input
        document.getElementById('file-input').addEventListener('change', (e) => this.handleFileUpload(e));

        // Load sample button
        document.getElementById('load-sample').addEventListener('click', () => this.loadSampleData());

        // Close code panel
        document.getElementById('close-code-panel').addEventListener('click', () => {
            document.getElementById('code-panel').classList.add('hidden');
        });

        // Window resize
        window.addEventListener('resize', () => this.render());
    }

    handleZoom(event) {
        const { transform } = event;
        this.currentZoom = transform.k;
        this.zoomGroup.attr('transform', transform);

        // Update slider
        document.getElementById('zoom-slider').value = transform.k;

        // Update zoom level indicator
        this.updateZoomLevelIndicator();

        // Update node detail based on zoom level
        this.updateNodeDetail();
    }

    updateZoomLevelIndicator() {
        const level = this.getZoomLevel();
        const badge = document.getElementById('current-level');
        badge.textContent = level.name;

        // Update sidebar indicators
        document.querySelectorAll('.zoom-info').forEach(el => {
            el.classList.remove('active');
        });

        const levelNum = level === this.zoomLevels.ARCHITECTURE ? 1 :
                        level === this.zoomLevels.SIGNATURES ? 2 : 3;
        const activeInfo = document.querySelector(`.zoom-info[data-level="${levelNum}"]`);
        if (activeInfo) activeInfo.classList.add('active');
    }

    getZoomLevel() {
        if (this.currentZoom < this.zoomLevels.ARCHITECTURE.max) {
            return this.zoomLevels.ARCHITECTURE;
        } else if (this.currentZoom < this.zoomLevels.SIGNATURES.max) {
            return this.zoomLevels.SIGNATURES;
        }
        return this.zoomLevels.CODE;
    }

    zoomBy(factor) {
        this.svg.transition()
            .duration(300)
            .call(this.zoom.scaleBy, factor);
    }

    setZoom(scale) {
        this.svg.transition()
            .duration(300)
            .call(this.zoom.scaleTo, scale);
    }

    resetView() {
        const container = document.getElementById('canvas-container');
        const width = container.clientWidth - 220;
        const height = container.clientHeight;

        this.svg.transition()
            .duration(500)
            .call(this.zoom.transform, d3.zoomIdentity.translate(width / 4, height / 4).scale(1));
    }

    async handleFileUpload(event) {
        const files = event.target.files;
        if (!files.length) return;

        const modules = [];

        for (const file of files) {
            if (file.name.endsWith('.py')) {
                try {
                    const content = await file.text();
                    const parsed = this.parseCode(content, file.name);
                    if (parsed) modules.push(parsed);
                } catch (err) {
                    console.error(`Error reading ${file.name}:`, err);
                }
            }
        }

        if (modules.length > 0) {
            this.modules = modules;
            this.render();
        }
    }

    parseCode(source, filename) {
        // Client-side Python parsing (simplified)
        // For full parsing, use the server endpoint
        const module = {
            name: filename.replace('.py', ''),
            path: filename,
            docstring: null,
            imports: [],
            import_from: {},
            classes: [],
            functions: [],
            code: source
        };

        const lines = source.split('\n');
        let currentClass = null;
        let inClass = false;
        let classIndent = 0;

        // Extract module docstring
        const docstringMatch = source.match(/^(['\"]{3})([\s\S]*?)\1/m);
        if (docstringMatch) {
            module.docstring = docstringMatch[2].trim();
        }

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();
            const indent = line.length - line.trimStart().length;

            // Import statements
            if (trimmed.startsWith('import ')) {
                const imported = trimmed.substring(7).split(',').map(s => s.trim().split(' ')[0]);
                module.imports.push(...imported);
            } else if (trimmed.startsWith('from ')) {
                const match = trimmed.match(/from\s+([\w.]+)\s+import\s+(.+)/);
                if (match) {
                    const moduleName = match[1];
                    const items = match[2].split(',').map(s => s.trim().split(' ')[0]);
                    if (!module.import_from[moduleName]) module.import_from[moduleName] = [];
                    module.import_from[moduleName].push(...items);
                }
            }
            // Class definition
            else if (trimmed.startsWith('class ')) {
                const match = trimmed.match(/class\s+(\w+)(?:\((.*?)\))?:/);
                if (match) {
                    if (currentClass) {
                        module.classes.push(currentClass);
                    }
                    currentClass = {
                        name: match[1],
                        docstring: null,
                        bases: match[2] ? match[2].split(',').map(s => s.trim()) : [],
                        methods: [],
                        lineno: i + 1,
                        end_lineno: i + 1
                    };
                    inClass = true;
                    classIndent = indent;

                    // Check for docstring
                    if (i + 1 < lines.length) {
                        const nextLine = lines[i + 1].trim();
                        if (nextLine.startsWith('"""') || nextLine.startsWith("'''")) {
                            const quote = nextLine.substring(0, 3);
                            if (nextLine.endsWith(quote) && nextLine.length > 6) {
                                currentClass.docstring = nextLine.slice(3, -3);
                            }
                        }
                    }
                }
            }
            // Function/method definition
            else if (trimmed.startsWith('def ') || trimmed.startsWith('async def ')) {
                const isAsync = trimmed.startsWith('async');
                const defPart = isAsync ? trimmed.substring(10) : trimmed.substring(4);
                const match = defPart.match(/(\w+)\s*\((.*?)\)(?:\s*->\s*(.+?))?:/);

                if (match) {
                    const func = {
                        name: match[1],
                        signature: (isAsync ? 'async ' : '') + 'def ' + match[1] + '(' + match[2] + ')' + (match[3] ? ' -> ' + match[3] : '') + ':',
                        docstring: null,
                        code: this.extractFunctionCode(lines, i),
                        lineno: i + 1,
                        end_lineno: i + 1,
                        decorators: [],
                        calls: this.extractCalls(this.extractFunctionCode(lines, i))
                    };

                    // Check for decorators (look back)
                    let j = i - 1;
                    while (j >= 0 && lines[j].trim().startsWith('@')) {
                        func.decorators.unshift(lines[j].trim().substring(1));
                        j--;
                    }

                    // Check for docstring
                    if (i + 1 < lines.length) {
                        const nextLine = lines[i + 1].trim();
                        if (nextLine.startsWith('"""') || nextLine.startsWith("'''")) {
                            const quote = nextLine.substring(0, 3);
                            if (nextLine.endsWith(quote) && nextLine.length > 6) {
                                func.docstring = nextLine.slice(3, -3);
                            }
                        }
                    }

                    if (inClass && indent > classIndent) {
                        currentClass.methods.push(func);
                        currentClass.end_lineno = func.end_lineno;
                    } else {
                        if (currentClass) {
                            module.classes.push(currentClass);
                            currentClass = null;
                            inClass = false;
                        }
                        module.functions.push(func);
                    }
                }
            }
        }

        if (currentClass) {
            module.classes.push(currentClass);
        }

        return module;
    }

    extractFunctionCode(lines, startIndex) {
        const startIndent = lines[startIndex].length - lines[startIndex].trimStart().length;
        let endIndex = startIndex + 1;

        while (endIndex < lines.length) {
            const line = lines[endIndex];
            if (line.trim() === '') {
                endIndex++;
                continue;
            }
            const currentIndent = line.length - line.trimStart().length;
            if (currentIndent <= startIndent && line.trim() !== '') {
                break;
            }
            endIndex++;
        }

        return lines.slice(startIndex, endIndex).join('\n');
    }

    extractCalls(code) {
        const calls = new Set();
        const regex = /\b(\w+)\s*\(/g;
        let match;
        while ((match = regex.exec(code)) !== null) {
            const name = match[1];
            if (!['def', 'class', 'if', 'for', 'while', 'with', 'except', 'print', 'return', 'async'].includes(name)) {
                calls.add(name);
            }
        }
        return Array.from(calls);
    }

    loadSampleData() {
        // Sample Python code to demonstrate the visualizer
        const sampleCode = `"""
Sample Python Module for Graphical Code Editor Demo
This module demonstrates the three zoom levels:
1. Architecture view - see modules, classes, and their relationships
2. Signatures view - see function signatures
3. Code view - see full source code
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class User:
    """Represents a user in the system"""
    id: int
    name: str
    email: str
    is_active: bool = True


class Database:
    """Database connection handler"""

    def __init__(self, connection_string: str):
        """Initialize database connection"""
        self.connection_string = connection_string
        self.connection = None

    def connect(self) -> bool:
        """Establish database connection"""
        # Simulated connection
        self.connection = True
        return True

    def disconnect(self):
        """Close database connection"""
        self.connection = None

    def query(self, sql: str) -> List[Dict]:
        """Execute SQL query and return results"""
        if not self.connection:
            self.connect()
        return []


class UserService:
    """Service for managing users"""

    def __init__(self, db: Database):
        """Initialize with database connection"""
        self.db = db
        self.cache: Dict[int, User] = {}

    def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID"""
        if user_id in self.cache:
            return self.cache[user_id]

        results = self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
        if results:
            user = User(**results[0])
            self.cache[user_id] = user
            return user
        return None

    def create_user(self, name: str, email: str) -> User:
        """Create a new user"""
        user = User(id=len(self.cache) + 1, name=name, email=email)
        self.cache[user.id] = user
        return user

    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        user = self.get_user(user_id)
        if user:
            user.is_active = False
            return True
        return False


class APIHandler:
    """REST API request handler"""

    def __init__(self, user_service: UserService):
        """Initialize with user service"""
        self.user_service = user_service

    def handle_get_user(self, request: Dict) -> Dict:
        """Handle GET /users/{id} request"""
        user_id = request.get('user_id')
        user = self.user_service.get_user(user_id)
        if user:
            return {'status': 200, 'data': user.__dict__}
        return {'status': 404, 'error': 'User not found'}

    def handle_create_user(self, request: Dict) -> Dict:
        """Handle POST /users request"""
        name = request.get('name')
        email = request.get('email')
        user = self.user_service.create_user(name, email)
        return {'status': 201, 'data': user.__dict__}


def initialize_app() -> APIHandler:
    """Initialize the application with all dependencies"""
    db = Database("postgresql://localhost/myapp")
    user_service = UserService(db)
    api = APIHandler(user_service)
    return api


def main():
    """Main entry point"""
    app = initialize_app()
    print("Application initialized successfully")


if __name__ == "__main__":
    main()
`;

        const module = this.parseCode(sampleCode, 'sample_app.py');
        this.modules = [module];
        this.render();
        this.updateModuleList();
    }

    updateModuleList() {
        const list = document.getElementById('module-list');
        list.innerHTML = '';

        this.modules.forEach((module, index) => {
            const li = document.createElement('li');
            li.textContent = module.name;
            li.addEventListener('click', () => this.focusOnModule(index));
            list.appendChild(li);
        });
    }

    focusOnModule(index) {
        const node = this.nodesLayer.select(`.module-${index}`);
        if (!node.empty()) {
            const bbox = node.node().getBBox();
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth - 220;
            const height = container.clientHeight;

            this.svg.transition()
                .duration(500)
                .call(this.zoom.transform,
                    d3.zoomIdentity
                        .translate(width / 2 - bbox.x - bbox.width / 2, height / 2 - bbox.y - bbox.height / 2)
                        .scale(1)
                );
        }
    }

    render() {
        this.nodesLayer.selectAll('*').remove();
        this.linksLayer.selectAll('*').remove();

        if (this.modules.length === 0) return;

        const layout = this.calculateLayout();
        this.renderLinks(layout);
        this.renderNodes(layout);
        this.updateNodeDetail();
    }

    calculateLayout() {
        const nodes = [];
        const links = [];

        let x = 50;
        let y = 50;
        const moduleWidth = this.nodeWidth + 40;

        // Build a map of all class names for relationship detection
        const classMap = new Map();
        this.modules.forEach((module, moduleIndex) => {
            module.classes.forEach((cls, classIndex) => {
                classMap.set(cls.name, { moduleIndex, classIndex });
            });
        });

        this.modules.forEach((module, moduleIndex) => {
            const moduleNode = {
                type: 'module',
                data: module,
                moduleIndex,
                x,
                y,
                width: this.nodeWidth,
                height: this.calculateModuleHeight(module)
            };
            nodes.push(moduleNode);

            // Add class nodes
            let classY = y + 50;
            module.classes.forEach((cls, classIndex) => {
                const classNode = {
                    type: 'class',
                    data: cls,
                    moduleIndex,
                    classIndex,
                    x: x + 20,
                    y: classY,
                    width: this.nodeWidth - 40,
                    height: this.calculateClassHeight(cls)
                };
                nodes.push(classNode);

                // Inheritance links
                cls.bases.forEach(base => {
                    if (classMap.has(base)) {
                        const parent = classMap.get(base);
                        links.push({
                            type: 'inheritance',
                            source: classNode,
                            target: { moduleIndex: parent.moduleIndex, classIndex: parent.classIndex }
                        });
                    }
                });

                classY += classNode.height + 20;
            });

            // Add function nodes
            module.functions.forEach((func, funcIndex) => {
                const funcNode = {
                    type: 'function',
                    data: func,
                    moduleIndex,
                    funcIndex,
                    x: x + 20,
                    y: classY,
                    width: this.nodeWidth - 40,
                    height: this.calculateFunctionHeight(func)
                };
                nodes.push(funcNode);
                classY += funcNode.height + 15;
            });

            // Update module height
            moduleNode.height = Math.max(moduleNode.height, classY - y + 20);

            x += moduleWidth + 100;
        });

        // Add import links
        this.modules.forEach((module, sourceIndex) => {
            const allImports = [...module.imports];
            Object.keys(module.import_from).forEach(key => allImports.push(key));

            allImports.forEach(imp => {
                const targetIndex = this.modules.findIndex(m =>
                    m.name === imp || imp.includes(m.name)
                );
                if (targetIndex !== -1 && targetIndex !== sourceIndex) {
                    links.push({
                        type: 'import',
                        sourceModule: sourceIndex,
                        targetModule: targetIndex
                    });
                }
            });
        });

        return { nodes, links };
    }

    calculateModuleHeight(module) {
        let height = 60; // Header
        module.classes.forEach(cls => {
            height += this.calculateClassHeight(cls) + 20;
        });
        module.functions.forEach(func => {
            height += this.calculateFunctionHeight(func) + 15;
        });
        return Math.max(height, 100);
    }

    calculateClassHeight(cls) {
        const level = this.getZoomLevel();
        if (level === this.zoomLevels.ARCHITECTURE) {
            return 50;
        } else if (level === this.zoomLevels.SIGNATURES) {
            return 50 + cls.methods.length * 20;
        }
        return 50 + cls.methods.length * 25;
    }

    calculateFunctionHeight(func) {
        const level = this.getZoomLevel();
        if (level === this.zoomLevels.ARCHITECTURE) {
            return 40;
        } else if (level === this.zoomLevels.SIGNATURES) {
            return 50;
        }
        const lines = func.code.split('\n').length;
        return Math.min(50 + lines * 12, 300);
    }

    renderNodes(layout) {
        const { nodes } = layout;
        const self = this;

        nodes.forEach(node => {
            if (node.type === 'module') {
                this.renderModuleNode(node);
            } else if (node.type === 'class') {
                this.renderClassNode(node);
            } else if (node.type === 'function') {
                this.renderFunctionNode(node);
            }
        });
    }

    renderModuleNode(node) {
        const group = this.nodesLayer.append('g')
            .attr('class', `node module module-${node.moduleIndex}`)
            .attr('transform', `translate(${node.x}, ${node.y})`);

        group.append('rect')
            .attr('width', node.width)
            .attr('height', node.height)
            .attr('rx', 8);

        // Module icon and name
        group.append('text')
            .attr('class', 'node-label node-icon')
            .attr('x', 12)
            .attr('y', 24)
            .text('📦');

        group.append('text')
            .attr('class', 'node-label node-title')
            .attr('x', 36)
            .attr('y', 24)
            .text(node.data.name);

        // Add click handler
        group.on('click', () => this.showCodePanel(node.data.name, node.data.code));

        // Tooltip
        group.on('mouseenter', (event) => this.showTooltip(event, node))
            .on('mouseleave', () => this.hideTooltip());
    }

    renderClassNode(node) {
        const group = this.nodesLayer.append('g')
            .attr('class', `node class class-${node.moduleIndex}-${node.classIndex}`)
            .attr('transform', `translate(${node.x}, ${node.y})`);

        const height = this.calculateClassHeight(node.data);

        group.append('rect')
            .attr('width', node.width)
            .attr('height', height)
            .attr('rx', 6);

        // Class icon and name
        group.append('text')
            .attr('class', 'node-label node-icon')
            .attr('x', 10)
            .attr('y', 22)
            .text('🔷');

        group.append('text')
            .attr('class', 'node-label node-title')
            .attr('x', 32)
            .attr('y', 22)
            .text(node.data.name);

        // Show methods based on zoom level
        const level = this.getZoomLevel();
        if (level !== this.zoomLevels.ARCHITECTURE) {
            node.data.methods.forEach((method, i) => {
                const methodGroup = group.append('g')
                    .attr('class', 'method-item')
                    .attr('transform', `translate(10, ${40 + i * 20})`);

                if (level === this.zoomLevels.SIGNATURES) {
                    methodGroup.append('text')
                        .attr('class', 'node-label node-signature')
                        .text(this.truncate(method.signature, 25));
                } else {
                    methodGroup.append('text')
                        .attr('class', 'node-label node-signature')
                        .text(this.truncate(method.signature, 25));
                }

                methodGroup.style('cursor', 'pointer')
                    .on('click', (event) => {
                        event.stopPropagation();
                        this.showCodePanel(method.name, method.code);
                    });
            });
        }

        // Add click handler
        group.on('click', () => {
            const classCode = node.data.methods.map(m => m.code).join('\n\n');
            this.showCodePanel(node.data.name, classCode);
        });

        group.on('mouseenter', (event) => this.showTooltip(event, node))
            .on('mouseleave', () => this.hideTooltip());
    }

    renderFunctionNode(node) {
        const group = this.nodesLayer.append('g')
            .attr('class', `node function function-${node.moduleIndex}-${node.funcIndex}`)
            .attr('transform', `translate(${node.x}, ${node.y})`);

        const height = this.calculateFunctionHeight(node.data);

        group.append('rect')
            .attr('width', node.width)
            .attr('height', height)
            .attr('rx', 6);

        // Function icon and name
        group.append('text')
            .attr('class', 'node-label node-icon')
            .attr('x', 10)
            .attr('y', 22)
            .text('⚡');

        const level = this.getZoomLevel();

        if (level === this.zoomLevels.ARCHITECTURE) {
            group.append('text')
                .attr('class', 'node-label node-title')
                .attr('x', 32)
                .attr('y', 22)
                .text(node.data.name);
        } else if (level === this.zoomLevels.SIGNATURES) {
            group.append('text')
                .attr('class', 'node-label node-signature')
                .attr('x', 10)
                .attr('y', 40)
                .text(this.truncate(node.data.signature, 30));
        } else {
            // CODE level - show truncated code
            group.append('text')
                .attr('class', 'node-label node-signature')
                .attr('x', 10)
                .attr('y', 40)
                .text(this.truncate(node.data.signature, 30));

            const codeLines = node.data.code.split('\n').slice(1, 8);
            codeLines.forEach((line, i) => {
                group.append('text')
                    .attr('class', 'node-label node-code')
                    .attr('x', 10)
                    .attr('y', 55 + i * 12)
                    .text(this.truncate(line, 35));
            });

            if (node.data.code.split('\n').length > 8) {
                group.append('text')
                    .attr('class', 'node-label node-code')
                    .attr('x', 10)
                    .attr('y', 55 + 8 * 12)
                    .text('...');
            }
        }

        group.on('click', () => this.showCodePanel(node.data.name, node.data.code));

        group.on('mouseenter', (event) => this.showTooltip(event, node))
            .on('mouseleave', () => this.hideTooltip());
    }

    renderLinks(layout) {
        const { nodes, links } = layout;

        links.forEach(link => {
            if (link.type === 'import') {
                const sourceNode = nodes.find(n => n.type === 'module' && n.moduleIndex === link.sourceModule);
                const targetNode = nodes.find(n => n.type === 'module' && n.moduleIndex === link.targetModule);

                if (sourceNode && targetNode) {
                    this.renderLink(sourceNode, targetNode, 'import');
                }
            } else if (link.type === 'inheritance') {
                const sourceNode = nodes.find(n =>
                    n.type === 'class' &&
                    n.moduleIndex === link.source.moduleIndex &&
                    n.classIndex === link.source.classIndex
                );
                const targetNode = nodes.find(n =>
                    n.type === 'class' &&
                    n.moduleIndex === link.target.moduleIndex &&
                    n.classIndex === link.target.classIndex
                );

                if (sourceNode && targetNode) {
                    this.renderLink(sourceNode, targetNode, 'inheritance');
                }
            }
        });
    }

    renderLink(source, target, type) {
        const sourceX = source.x + source.width;
        const sourceY = source.y + source.height / 2;
        const targetX = target.x;
        const targetY = target.y + target.height / 2;

        const midX = (sourceX + targetX) / 2;

        const path = d3.path();
        path.moveTo(sourceX, sourceY);
        path.bezierCurveTo(midX, sourceY, midX, targetY, targetX, targetY);

        this.linksLayer.append('path')
            .attr('class', `link ${type}`)
            .attr('d', path.toString())
            .attr('marker-end', type === 'inheritance' ? 'url(#arrowhead-inheritance)' : 'url(#arrowhead)');
    }

    updateNodeDetail() {
        // Re-render with updated detail level
        // This is called when zoom changes
        const level = this.getZoomLevel();

        // Update class heights
        this.nodesLayer.selectAll('.node.class').each(function(d) {
            const group = d3.select(this);
            // Height adjustment is handled in render
        });

        // Could add progressive detail updates here
    }

    showTooltip(event, node) {
        const tooltip = document.getElementById('tooltip');
        let content = '';

        if (node.type === 'module') {
            content = `<h4>📦 ${node.data.name}</h4>`;
            if (node.data.docstring) {
                content += `<p>${node.data.docstring}</p>`;
            }
            content += `<p><strong>Classes:</strong> ${node.data.classes.length}</p>`;
            content += `<p><strong>Functions:</strong> ${node.data.functions.length}</p>`;
            if (node.data.imports.length > 0) {
                content += `<p><strong>Imports:</strong> ${node.data.imports.join(', ')}</p>`;
            }
        } else if (node.type === 'class') {
            content = `<h4>🔷 ${node.data.name}</h4>`;
            if (node.data.bases.length > 0) {
                content += `<p><strong>Inherits:</strong> ${node.data.bases.join(', ')}</p>`;
            }
            if (node.data.docstring) {
                content += `<p>${node.data.docstring}</p>`;
            }
            content += `<p><strong>Methods:</strong> ${node.data.methods.length}</p>`;
        } else if (node.type === 'function') {
            content = `<h4>⚡ ${node.data.name}</h4>`;
            content += `<pre><code>${this.escapeHtml(node.data.signature)}</code></pre>`;
            if (node.data.docstring) {
                content += `<p>${node.data.docstring}</p>`;
            }
            if (node.data.decorators.length > 0) {
                content += `<p><strong>Decorators:</strong> @${node.data.decorators.join(', @')}</p>`;
            }
        }

        tooltip.innerHTML = content;
        tooltip.style.left = `${event.pageX + 15}px`;
        tooltip.style.top = `${event.pageY + 15}px`;
        tooltip.classList.add('visible');
    }

    hideTooltip() {
        const tooltip = document.getElementById('tooltip');
        tooltip.classList.remove('visible');
    }

    showCodePanel(title, code) {
        const panel = document.getElementById('code-panel');
        const titleEl = document.getElementById('code-panel-title');
        const codeEl = document.getElementById('code-content');

        titleEl.textContent = title;
        codeEl.textContent = code;

        // Highlight code
        hljs.highlightElement(codeEl);

        panel.classList.remove('hidden');
    }

    truncate(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 3) + '...';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.editor = new GraphicalCodeEditor();
});
